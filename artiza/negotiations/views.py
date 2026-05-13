# negotiations/views.py
from rest_framework import generics, permissions, status, serializers
from rest_framework.views import APIView, PermissionDenied
from rest_framework.response import Response
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from updates.models import ProjectMessage

from .models import Negotiation, NegotiationMessage
from .serializers import NegotiationSerializer, NegotiationMessageSerializer
from .utils import should_block_negotiation_message
from proposals.models import Proposal
from notifications.utils import send_push_to_user


# -------------------------
# Unread Negotiations / Messages Count
# -------------------------
class UnreadNegotiationsCountView(APIView):
    """Get counts of unread negotiations and messages for the current user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.role == 'client':
            unread_negotiations_count = Negotiation.objects.filter(
                proposal__project__client=user,
                has_unread_client=True,
                is_closed=False
            ).count()
            
            unread_messages_count = NegotiationMessage.objects.filter(
                negotiation__proposal__project__client=user,
                read_by_client=False,
                blocked=False
            ).exclude(sender=user).count()
            
        elif user.role == 'artisan':
            unread_negotiations_count = Negotiation.objects.filter(
                proposal__artisan=user,
                has_unread_artisan=True,
                is_closed=False
            ).count()
            
            unread_messages_count = NegotiationMessage.objects.filter(
                negotiation__proposal__artisan=user,
                read_by_artisan=False,
                blocked=False
            ).exclude(sender=user).count()
            
        else:
            unread_negotiations_count = 0
            unread_messages_count = 0
        
        return Response({
            'unread_negotiations_count': unread_negotiations_count,
            'unread_messages_count': unread_messages_count,
            'total_unread': unread_negotiations_count + unread_messages_count
        })


# -------------------------
# List Negotiations with Unread Counts
# -------------------------


# class NegotiationListView(generics.ListAPIView):
#     serializer_class = NegotiationSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user
        
#         if user.role == 'client':
#             return Negotiation.objects.filter(
#                 proposal__project__client=user,
#                 # Remove the is_closed filter to show ALL negotiations
#                 # is_closed=False
#             ).annotate(
#                 unread_count=Count(
#                     'messages',
#                     filter=Q(messages__read_by_client=False) & ~Q(messages__sender=user) & Q(messages__blocked=False)
#                 )
#             ).order_by('-last_message_time')
            
#         elif user.role == 'artisan':
#             return Negotiation.objects.filter(
#                 proposal__artisan=user,
#                 # Remove the is_closed filter to show ALL negotiations
#                 # is_closed=False
#             ).annotate(
#                 unread_count=Count(
#                     'messages',
#                     filter=Q(messages__read_by_artisan=False) & ~Q(messages__sender=user) & Q(messages__blocked=False)
#                 )
#             ).order_by('-last_message_time')
        
#         return Negotiation.objects.none()






class NegotiationListView(generics.ListAPIView):
    serializer_class = NegotiationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'client':
            queryset = Negotiation.objects.filter(
                proposal__project__client=user,
            ).order_by('-last_message_time')
            
        elif user.role == 'artisan':
            queryset = Negotiation.objects.filter(
                proposal__artisan=user,
            ).order_by('-last_message_time')
        else:
            return Negotiation.objects.none()
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate unread counts manually and add to response
        user = request.user
        data = []
        
        for negotiation in queryset:
            negotiation_data = serializer.data[data.__len__()]
            
            # Calculate negotiation unread count
            if user.role == 'client':
                negotiation_unread = negotiation.messages.filter(
                    read_by_client=False,
                    blocked=False
                ).exclude(sender=user).count()
                
                # Calculate project updates unread count
                project_unread = ProjectMessage.objects.filter(
                    project=negotiation.proposal.project,
                    read_by_client=False,
                    blocked=False
                ).exclude(sender=user).count()
                
            else:  # artisan
                negotiation_unread = negotiation.messages.filter(
                    read_by_artisan=False,
                    blocked=False
                ).exclude(sender=user).count()
                
                # Calculate project updates unread count
                project_unread = ProjectMessage.objects.filter(
                    project=negotiation.proposal.project,
                    read_by_artisan=False,
                    blocked=False
                ).exclude(sender=user).count()
            
            # Combine both counts
            total_unread = negotiation_unread + project_unread
            
            negotiation_data['unread_count'] = total_unread
            negotiation_data['negotiation_unread'] = negotiation_unread
            negotiation_data['project_unread'] = project_unread
            
            data.append(negotiation_data)
        
        return Response(data)
    
    
    
    

# -------------------------
# List / Create Negotiation Messages
# -------------------------

class NegotiationMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = NegotiationMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        proposal_id = self.kwargs.get('proposal_id')
        return NegotiationMessage.objects.filter(
            negotiation__proposal_id=proposal_id,
            blocked=False
        ).order_by('timestamp')

    def perform_create(self, serializer):
        proposal_id = self.kwargs.get("proposal_id")
        sender = self.request.user

        negotiation, _ = Negotiation.objects.get_or_create(
            proposal_id=proposal_id
        )

        message_text = serializer.validated_data.get("message", "")

        flagged, blocked = should_block_negotiation_message(
            proposal_id, sender, message_text
        )

        message = serializer.save(
            negotiation=negotiation,
            sender=sender,
            flagged=flagged,
            blocked=blocked
        )

        if blocked:
            raise serializers.ValidationError({
                "detail": "Your message contains restricted content and cannot be delivered."
            })

        # 🔔 DETERMINE RECEIVER
        if sender.role == "client":
            receiver = negotiation.proposal.artisan
        else:
            receiver = negotiation.proposal.project.client

        url = "/artisan-dashboard" if receiver.role == "artisan" else "/client-dashboard"
        
        # 🔔 SEND PUSH
        send_push_to_user(
            user=receiver,
            title="New negotiation message",
            body=message.message[:100],
            data={
                "type": "negotiation",
                "proposal_id": str(proposal_id),
                "url": url
            },
            # data={
            #     "type": "project",
            #     "project_id": str(proposal_id),
            #     "url": f"/my-proposals/{proposal_id}" if receiver.role == "artisan" else f"/my-projects/{proposal_id}"
            # }
        )

# -------------------------
# Negotiation Detail
# -------------------------
class NegotiationDetailView(generics.RetrieveAPIView):
    serializer_class = NegotiationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        proposal_id = self.kwargs.get('proposal_id')
        user = self.request.user

        negotiation, _ = Negotiation.objects.get_or_create(
            proposal_id=proposal_id
        )

        # OPTIONAL: still enforce access control
        if user.role == 'client' and negotiation.proposal.project.client != user:
            raise PermissionDenied("Not allowed")

        if user.role == 'artisan' and negotiation.proposal.artisan != user:
            raise PermissionDenied("Not allowed")

        return negotiation
    
# -------------------------
# Submit / Accept Final Agreement
# -------------------------


class SubmitFinalAgreementView(generics.UpdateAPIView):
    serializer_class = NegotiationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Negotiation.objects.all()

    def patch(self, request, *args, **kwargs):
        negotiation = self.get_object()
        final_amount = request.data.get('final_agreed_amount')

        if not final_amount:
            return Response({'error': 'Final amount is required'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user != negotiation.proposal.artisan:
            return Response({'error': 'Only the artisan can submit final agreement'}, status=status.HTTP_403_FORBIDDEN)

        negotiation.pending_final_amount = final_amount
        negotiation.save()

        NegotiationMessage.objects.create(
            negotiation=negotiation,
            sender=request.user,
            message=f"Final agreement submitted: KSh {final_amount}",
            offer=final_amount
        )

        return Response({
            "status": "pending_final_amount_submitted",
            "pending_final_amount": final_amount
        })
        
        
        
class AcceptFinalAgreementView(generics.UpdateAPIView):
    serializer_class = NegotiationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Negotiation.objects.all()

    def patch(self, request, *args, **kwargs):
        negotiation = self.get_object()

        if request.user != negotiation.proposal.project.client:
            return Response({'error': 'Only the client can accept final agreement'}, status=status.HTTP_403_FORBIDDEN)

        if not negotiation.pending_final_amount:
            return Response({'error': 'No final agreement submitted yet'}, status=status.HTTP_400_BAD_REQUEST)

        # Set the final agreed amount
        negotiation.final_agreed_amount = negotiation.pending_final_amount
        # DO NOT close the negotiation - keep chat active for ongoing communication
        # negotiation.is_closed = True  # <-- COMMENT THIS OUT or REMOVE IT
        negotiation.save()

        # Update proposal price
        proposal = negotiation.proposal
        proposal.negotiated_price = negotiation.pending_final_amount
        proposal.save()

        # Mark final message as accepted
        final_message = negotiation.messages.filter(
            offer=negotiation.pending_final_amount,
            sender=negotiation.proposal.artisan
        ).first()

        if final_message:
            final_message.is_accepted = True
            final_message.save()

        return Response({
            'status': 'final_agreement_accepted',
            'final_agreed_amount': negotiation.final_agreed_amount,
            'is_closed': negotiation.is_closed  # This will now be False
        })
        
        
# -------------------------
# Proposal-specific Unread / Read APIs
# -------------------------
class ProposalUnreadCountView(APIView):
    """Get unread message count for a specific proposal"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, proposal_id):
        user = request.user

        if user.role == 'artisan':
            unread_count = NegotiationMessage.objects.filter(
                negotiation__proposal_id=proposal_id,
                read_by_artisan=False,
                sender__role='client',
                blocked=False
            ).count()
        else:
            unread_count = 0

        return Response({'unread_count': unread_count})


class MarkProposalMessagesAsReadView(APIView):
    """Mark all messages in a proposal as read for the artisan"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, proposal_id):
        user = request.user

        if user.role != 'artisan':
            return Response({'success': False, 'detail': 'Only artisans can mark messages as read'}, status=status.HTTP_403_FORBIDDEN)

        updated_count = NegotiationMessage.objects.filter(
            negotiation__proposal_id=proposal_id,
            read_by_artisan=False,
            sender__role='client',
            blocked=False
        ).update(read_by_artisan=True)

        negotiation = Negotiation.objects.filter(proposal_id=proposal_id).first()
        if negotiation:
            negotiation.has_unread_artisan = False
            negotiation.save()

        return Response({
            'success': True,
            'messages_marked_read': updated_count
        })