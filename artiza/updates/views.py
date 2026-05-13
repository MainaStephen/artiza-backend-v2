from rest_framework import permissions, status, generics, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from projects.models import ProjectRequest
from .models import ProjectMessage
from .serializers import (
    ProjectMessageSerializer,
    FlaggedMessageSerializer,
    ReviewFlaggedMessageSerializer
)
from .utils import should_block_message
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from negotiations.models import NegotiationMessage
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from projects.models import ProjectRequest
from .models import ProjectMessage
from .serializers import ProjectMessageSerializer
from .utils import should_block_message
from notifications.utils import send_push_to_user
from django.utils.dateparse import parse_datetime


class ProjectMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        user = request.user

        # Get project with proper permissions
        try:
            if user.role == "client":
                project = ProjectRequest.objects.get(id=project_id, client=user)
            elif user.role == "artisan":
                # For artisans, check if they have ANY proposal for this project
                project = ProjectRequest.objects.filter(
                    id=project_id,
                    proposals__artisan=user
                ).distinct().first()
                
                if not project:
                    return Response([], status=403)
            elif user.is_staff:
                project = ProjectRequest.objects.get(id=project_id)
            else:
                return Response([], status=403)
        except ProjectRequest.DoesNotExist:
            return Response({"detail": "Project not found"}, status=404)

        # ✅ FIX: Get ALL project messages (not just selected proposal)
        project_messages = ProjectMessage.objects.filter(
            project=project,
            blocked=False
        ).order_by("created_at")

        project_data = ProjectMessageSerializer(
            project_messages,
            many=True,
            context={"request": request}
        ).data

        for msg in project_data:
            msg["source"] = "project"

        # ✅ FIX: Get ALL negotiations for this project (not just selected proposal)
        # Include all proposals, not just selected ones
        negotiation_data = []
        
        # Get all proposals for this project
        proposals = project.proposals.all()
        
        for proposal in proposals:
            if hasattr(proposal, "negotiation"):
                negotiation_messages = proposal.negotiation.messages.filter(
                    blocked=False
                ).order_by("timestamp")

                for msg in negotiation_messages:
                    negotiation_data.append({
                        "id": f"neg-{msg.id}",
                        "sender_id": msg.sender.id,
                        "sender": msg.sender.id,
                        "sender_name": msg.sender.full_name,
                        "sender_role": msg.sender.role,
                        "type": "chat",
                        "message": msg.message,
                        "note": None,
                        "progress_percentage": 0,
                        "images": [],
                        "created_at": msg.timestamp.isoformat(),
                        "read_by_client": msg.read_by_client,
                        "read_by_artisan": msg.read_by_artisan,
                        "source": "negotiation",
                        "offer": msg.offer,
                        "is_accepted": msg.is_accepted,
                    })

        # Combine and sort
        combined = negotiation_data + project_data

        def get_datetime(val):
            if isinstance(val, str):
                from django.utils.dateparse import parse_datetime
                return parse_datetime(val)
            return val

        combined.sort(key=lambda x: get_datetime(x.get("created_at", "")) or get_datetime(x.get("timestamp", "")))

        return Response(combined)



class ProjectUpdatesPostView(generics.CreateAPIView):
    """Create a new message in the updates app (project messages)"""
    serializer_class = ProjectMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        user = self.request.user

        # Get the project
        try:
            project = ProjectRequest.objects.get(id=project_id)
        except ProjectRequest.DoesNotExist:
            raise serializers.ValidationError({"detail": "Project not found"})

        # Check permissions
        if user.role == "client" and project.client != user:
            raise serializers.ValidationError({"detail": "You don't have permission to post here"})
        
        if user.role == "artisan":
            # Check if artisan has a selected proposal for this project
            has_selected_proposal = project.proposals.filter(
                artisan=user,
                is_selected=True
            ).exists()
            
            if not has_selected_proposal:
                raise serializers.ValidationError({"detail": "You don't have permission to post here"})

        # Get message text for moderation
        message_text = self.request.data.get('message', '')
        note = self.request.data.get('note', '')
        combined_text = f"{message_text} {note}".strip()

        # Check for restricted content
        flagged, blocked = should_block_message(
            project_id=project_id,
            user=user,
            message_text=combined_text
        )

        if blocked:
            raise serializers.ValidationError({
                "detail": "Your message contains restricted content and cannot be delivered."
            })

        # Save the message
        message = serializer.save(
            project=project,
            sender=user,
            flagged=flagged,
            blocked=blocked
        )

        # Update project status for milestones
        if message.type == "milestone" and message.progress_percentage == 100:
            project.status = "completed"
            project.date_of_completion = timezone.now()
            project.save(update_fields=['status', 'date_of_completion'])
        elif message.type == "milestone" and message.progress_percentage > 0:
            if project.status != "in-progress":
                project.status = "in-progress"
                project.save(update_fields=['status'])

        # Send notification to the other party
        receiver = None
        if user.role == "client":
            # Find selected artisan
            selected_proposal = project.proposals.filter(is_selected=True).first()
            if selected_proposal:
                receiver = selected_proposal.artisan
        elif user.role == "artisan":
            receiver = project.client

        if receiver:
            url = "/artisan-dashboard" if receiver.role == "artisan" else "/client-dashboard"
            
            # Customize message based on type
            if message.type == "milestone":
                body = f"Milestone update: {message.progress_percentage}% complete - {message.note[:50]}..."
            else:
                body = message.message[:100] if message.message else "New project update"
            
            send_push_to_user(
                user=receiver,
                title="New project message",
                body=body,
                data={
                    "type": "project",
                    "project_id": str(project.id),
                    "url": url
                }
            )

        return message
    
# -------------------------
# Mark Messages Read 
# ------------------------- 
class CombinedMarkReadView(APIView):
    """Mark all messages (both project and negotiation) as read for a project"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_id):
        user = request.user
        
        try:
            # Get the project
            if user.role == "client":
                project = ProjectRequest.objects.get(id=project_id, client=user)
            elif user.role == "artisan":
                project = ProjectRequest.objects.filter(
                    id=project_id,
                    proposals__artisan=user
                ).distinct().first()
                if not project:
                    return Response({"detail": "Project not found"}, status=404)
            else:
                return Response({"detail": "Forbidden"}, status=403)
        except ProjectRequest.DoesNotExist:
            return Response({"detail": "Project not found"}, status=404)

        marked_count = {
            'project_messages': 0,
            'negotiation_messages': 0,
            'negotiations': 0
        }

        # 1. Mark project messages as read
        if user.role == "client":
            project_messages = ProjectMessage.objects.filter(
                project=project,
                read_by_client=False,
                blocked=False
            ).exclude(sender=user)
            marked_count['project_messages'] = project_messages.update(read_by_client=True)
            
            # Optional: Update project last read - REMOVED since field doesn't exist
            # if hasattr(project, 'client_last_read'):
            #     project.client_last_read = timezone.now()
            #     project.save(update_fields=['client_last_read'])
            
        elif user.role == "artisan":
            project_messages = ProjectMessage.objects.filter(
                project=project,
                read_by_artisan=False,
                blocked=False
            ).exclude(sender=user)
            marked_count['project_messages'] = project_messages.update(read_by_artisan=True)
            
            # Optional: Update project last read - REMOVED since field doesn't exist
            # if hasattr(project, 'artisan_last_read'):
            #     project.artisan_last_read = timezone.now()
            #     project.save(update_fields=['artisan_last_read'])

        # 2. Mark negotiation messages as read for all proposals in this project
        proposals = project.proposals.all()
        
        for proposal in proposals:
            if hasattr(proposal, 'negotiation'):
                negotiation = proposal.negotiation
                
                if user.role == "client":
                    # Mark negotiation messages as read for client
                    neg_messages = NegotiationMessage.objects.filter(
                        negotiation=negotiation,
                        read_by_client=False,
                        blocked=False
                    ).exclude(sender=user)
                    count = neg_messages.update(read_by_client=True)
                    marked_count['negotiation_messages'] += count
                    
                    # Update negotiation has_unread status
                    if negotiation.has_unread_client:
                        negotiation.has_unread_client = False
                        negotiation.save(update_fields=['has_unread_client'])
                        marked_count['negotiations'] += 1
                        
                elif user.role == "artisan":
                    # Mark negotiation messages as read for artisan
                    neg_messages = NegotiationMessage.objects.filter(
                        negotiation=negotiation,
                        read_by_artisan=False,
                        blocked=False
                    ).exclude(sender=user)
                    count = neg_messages.update(read_by_artisan=True)
                    marked_count['negotiation_messages'] += count
                    
                    # Update negotiation has_unread status
                    if negotiation.has_unread_artisan:
                        negotiation.has_unread_artisan = False
                        negotiation.save(update_fields=['has_unread_artisan'])
                        marked_count['negotiations'] += 1

        return Response({
            'success': True,
            'marked_read': marked_count,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)        



# -------------------------
# Admin: View Flagged Messages
# -------------------------
class FlaggedMessagesView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = FlaggedMessageSerializer

    def get_queryset(self):
        # Only messages that are flagged and not reviewed yet
        return ProjectMessage.objects.filter(flagged=True, reviewed_by_admin=False).order_by("-created_at")


# -------------------------
# Admin: Review a Flagged Message
# -------------------------
class ReviewFlaggedMessageView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, message_id):
        try:
            message = ProjectMessage.objects.get(id=message_id, flagged=True)
        except ProjectMessage.DoesNotExist:
            return Response({"detail": "Message not found or not flagged"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewFlaggedMessageSerializer(data=request.data)
        if serializer.is_valid():
            # Mark as reviewed
            message.reviewed_by_admin = True
            message.reviewed_at = timezone.now()
            message.review_message = serializer.validated_data.get("review_message", "")
            # Optionally unblock the message if admin approves
            if serializer.validated_data.get("unblock", False):
                message.blocked = False
            message.save()
            return Response({"detail": "Message reviewed successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    

# class CombinedProjectMessagesView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request, project_id):
#         user = request.user
        
#         # Get project
#         try:
#             if user.role == "client":
#                 project = ProjectRequest.objects.get(id=project_id, client=user)
#             elif user.role == "artisan":
#                 project = ProjectRequest.objects.filter(
#                     id=project_id,
#                     proposals__artisan=user
#                 ).distinct().first()
#                 if not project:
#                     return Response([], status=403)
#             else:
#                 return Response([], status=403)
#         except ProjectRequest.DoesNotExist:
#             return Response({"detail": "Project not found"}, status=404)
        
#         messages = []
        
#         # Get project messages
#         project_msgs = ProjectMessage.objects.filter(
#             project=project, blocked=False
#         ).order_by('created_at')
        
#         for msg in project_msgs:
#             messages.append({
#                 'id': f'proj-{msg.id}',
#                 'message': msg.message,
#                 'sender_role': msg.sender.role,
#                 'sender_name': msg.sender.full_name,
#                 'created_at': msg.created_at.isoformat(),
#                 'type': msg.type,
#                 'source': 'project',
#                 'read_by_client': msg.read_by_client,
#                 'read_by_artisan': msg.read_by_artisan,
#             })
        
#         # Get negotiation messages from ALL proposals
#         for proposal in project.proposals.all():
#             if hasattr(proposal, 'negotiation'):
#                 neg_msgs = proposal.negotiation.messages.filter(blocked=False).order_by('timestamp')
#                 for msg in neg_msgs:
#                     messages.append({
#                         'id': f'neg-{msg.id}',
#                         'message': msg.message,
#                         'sender_role': msg.sender.role,
#                         'sender_name': msg.sender.full_name,
#                         'created_at': msg.timestamp.isoformat(),
#                         'type': 'chat',
#                         'source': 'negotiation',
#                         'read_by_client': msg.read_by_client,
#                         'read_by_artisan': msg.read_by_artisan,
#                         'offer': msg.offer,
#                         'is_accepted': msg.is_accepted,
#                     })
        
#         # Sort by created_at
#         messages.sort(key=lambda x: x['created_at'])
        
#         return Response(messages)