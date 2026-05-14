
from django.forms import DecimalField
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q, Exists, OuterRef, Subquery, DateTimeField, Max,IntegerField
from django.db.models import DecimalField 
from django.utils.timezone import localtime
from .models import ProjectRequest,ProjectImage,ReadyMadeProduct,ProductImage
from .serializers import (
    ProjectRequestOpenSerializer,
    ProjectRequestClientUpdatesSerializer,
    ProjectRequestCreateSerializer,
    ProjectRequestBaseSerializer,
    ClientProjectRequestSerializer,
    ProjectImageSerializer,
    ArtisanAcceptedProjectsSerializer,
    ReadyMadeProductSerializer,
)
from proposals.models import Proposal
from updates.models import ProjectMessage
from django.db.models import Count, Q, Subquery, Case, When, Value, F
from django.db import models
from negotiations.models import Negotiation, NegotiationMessage
from users.models import User  
from updates.models import ProjectMessage
from django.db.models.functions import Coalesce
from artisanmatching.models import ArtisanMatch
from .serializers import ArtisanMatchedProjectSerializer
from artisanmatching.models import ArtisanMatch
from users.models import ArtisanProfile
from notifications.utils import send_push_to_user
from django.shortcuts import get_object_or_404
from .serializers import (
    ArtisanMatchedProjectSerializer,
    ProjectMatchedArtisanSerializer,
)

# ----------------------------
# CLIENT VIEWS
# ----------------------------

# creates projects then calls the auto assignment of artisans to projects
class ClientRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectRequestCreateSerializer
        return ProjectRequestBaseSerializer

    def get_queryset(self):
        return ProjectRequest.objects.filter(
            client=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        project = serializer.save(client=self.request.user)   

        from artisanmatching.services import match_artisans_to_project       

        match_artisans_to_project(project)

       
        
        
class ClientRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectRequestBaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProjectRequest.objects.filter(client=self.request.user)
    
    
class ClientProjectsWithUpdatesView(generics.ListAPIView):
    """
    List in-progress projects for a client,
    annotated with:
      - unread_updates_count
      - last_update_time (latest message timestamp)
      - progress (maximum progress_percentage from all messages)
    """
    serializer_class = ProjectRequestClientUpdatesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != "client":
            return ProjectRequest.objects.none()

        # Subquery to get the latest message timestamp
        last_update_subquery = ProjectMessage.objects.filter(
            project=OuterRef("pk")
        ).order_by("-created_at").values("created_at")[:1]

        queryset = (
            ProjectRequest.objects.annotate(
                unread_updates_count=Count(
                    "messages",
                    filter=Q(messages__read_by_client=False, messages__blocked=False)
                ),
                last_update_time=Subquery(
                    last_update_subquery,
                    output_field=DateTimeField()
                ),
                progress=Max("messages__progress_percentage")  
            )
            .filter(client=user, status__in=["in-progress", "completed"])
            .order_by("-created_at")
        )

        return queryset

# ----------------------------
# ARTISAN VIEWS
# ----------------------------





class ListArtisanAcceptedProjects(generics.ListAPIView):
    serializer_class = ArtisanAcceptedProjectsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != "artisan":
            return ProjectRequest.objects.none()

        # IDs of projects where this artisan has a selected proposal
        accepted_ids = Proposal.objects.filter(
            artisan=user, is_selected=True
        ).values_list("project_id", flat=True)

        # Subquery: latest milestone message's progress (ignore blocked)
        latest_progress = ProjectMessage.objects.filter(
            project=OuterRef("pk"),
            type="milestone",
            blocked=False
        ).order_by("-created_at").values("progress_percentage")[:1]

        # Annotate unread updates for artisan (not blocked/flagged, not sent by artisan themselves)
        unread_updates_count = Count(
            "messages",
            filter=Q(messages__read_by_artisan=False, messages__blocked=False, messages__flagged=False) & ~Q(messages__sender=user)
        )

        queryset = (
            ProjectRequest.objects.filter(id__in=accepted_ids)
            .annotate(
                progress=Subquery(latest_progress, output_field=IntegerField()),
                unread_updates=unread_updates_count
            )
            .order_by("-created_at")
        )

        return queryset




class ListClientProjectsView(generics.ListAPIView):
    serializer_class = ClientProjectRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != "client":
            return ProjectRequest.objects.none()

        # Subquery 1: Fetch final agreed amount from closed negotiation
        negotiation_qs = Negotiation.objects.filter(
            proposal__project=OuterRef("pk"),
            final_agreed_amount__isnull=False,
            
        ).values("final_agreed_amount")[:1]

        # Subquery 2: Fetch proposed price from selected proposal (when no negotiation)
        selected_proposal_qs = Proposal.objects.filter(
            project=OuterRef("pk"),
            is_selected=True
        ).values("proposed_price")[:1]

        # Add annotation for unread negotiation messages
        unread_negotiation_messages = Count(
            'proposals__negotiation__messages',
            filter=Q(
                proposals__negotiation__messages__read_by_client=False,
                proposals__negotiation__messages__sender__role='artisan',
                proposals__negotiation__messages__flagged='False',
                proposals__negotiation__messages__blocked='False',
            )
        )

        return (
            ProjectRequest.objects.filter(client=user)
            .annotate(
                # proposals_count=Count(
                #     "proposals",
                #     # filter=Q(proposals__is_selected=False)
                # ),
                proposals_count = Count("proposals", filter=Q(proposals__is_selected=False) ,distinct=True),
                # First try to get negotiated cost, fallback to selected proposal price
                negotiated_cost=Subquery(negotiation_qs, output_field=models.DecimalField()),
                selected_proposal_price=Subquery(selected_proposal_qs, output_field=models.DecimalField()),
                agreed_cost=Case(
                    When(negotiated_cost__isnull=False, then=F('negotiated_cost')),
                    When(selected_proposal_price__isnull=False, then=F('selected_proposal_price')),
                    default=Value(None),
                    output_field=models.DecimalField()
                ),
                unread_negotiation_messages=unread_negotiation_messages
            )
            .order_by("-created_at")
        )
        
from django.db.models import Count, Q, OuterRef, Subquery, Max



class ClientDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "client":
            return Response({"detail": "Access denied."}, status=403)

        # Fetch all projects for client
        projects = ProjectRequest.objects.filter(client=user)
        completed_projects = projects.filter(status="completed").count()
        ongoing_projects = projects.filter(status="in-progress").count()
        open_projects = projects.filter(status="open").count()

        # Prepare project data
        projects_data = []
        total_proposals_count = 0
        total_unread_updates = 0

        for project in projects:
            # Proposals count (exclude if a proposal is selected)
            proposals_count = 0 if project.proposals.filter(is_selected=True).exists() else project.proposals.count()
            total_proposals_count += proposals_count

            # Unread project updates (exclude blocked/flagged)
            unread_updates = project.messages.filter(
                read_by_client=False,
                blocked=False,
                flagged=False
            ).count()
            total_unread_updates += unread_updates

            # Artisan info for ongoing/completed projects
            artisan_info = None
            if project.status in ["in-progress", "completed"]:
                selected_proposal = project.proposals.filter(is_selected=True).first()
                if selected_proposal:
                    artisan_info = {
                        "name": selected_proposal.artisan.full_name,
                        "rating": getattr(selected_proposal.artisan, 'rating', 4.5)
                    }

            projects_data.append({
                "id": project.id,
                "title": project.title,
                "status": project.status,
                "proposals_count": proposals_count,
                "deadline": project.deadline,
                "description": project.description,
                "unread_updates": unread_updates,
                "artisan": artisan_info,
                "budget": project.budget,
                "created_at": localtime(project.created_at).strftime("%b %d, %Y"),
            })

        # =========================================================
        # UPDATED: Ongoing projects - SHOW HIGHEST PROGRESS EVER ACHIEVED
        # =========================================================
        ongoing_projects_data = []
        for project in projects.filter(status="in-progress"):
            # Get the HIGHEST progress percentage ever achieved (not just latest)
            highest_progress = (
                ProjectMessage.objects
                .filter(
                    project=project,
                    type='milestone',
                    blocked=False,
                    flagged=False
                )
                .aggregate(max_progress=Max('progress_percentage'))
                .get('max_progress') or 0
            )
            
            # Also get the latest message for other info (photo, timestamp)
            latest_update = ProjectMessage.objects.filter(
                project=project,
                blocked=False,
                flagged=False
            ).order_by("-created_at").first()
            
            has_photo = latest_update.images.exists() if latest_update else False
            
            # Determine next milestone based on HIGHEST progress
            if highest_progress < 50:
                next_step = "Material Preparation"
            elif highest_progress < 80:
                next_step = "Assembly"
            elif highest_progress < 100:
                next_step = "Final Quality Check"
            else:
                next_step = "Quality Assurance Check"

            # Artisan name
            selected_proposal = project.proposals.filter(is_selected=True).first()
            artisan_name = selected_proposal.artisan.full_name if selected_proposal else None

            ongoing_projects_data.append({
                "id": project.id,
                "title": project.title,
                "progress": highest_progress,  # Use the highest progress value
                "next_milestone": next_step,
                "due_date": project.deadline,
                "has_photo": has_photo,
                "artisan_name": artisan_name,
                "last_update": localtime(latest_update.created_at).strftime("%b %d, %H:%M") if latest_update else None,
            })

        unread_negotiation_messages_count = NegotiationMessage.objects.filter(
            negotiation__proposal__project__client=user,
            read_by_client=False,
            blocked=False,
            flagged=False,
            sender__role='artisan'
        ).count()

        # Active negotiations
        active_negotiations = Negotiation.objects.filter(
            proposal__project__client=user,
          
        ).annotate(
            unread_message_count=Count(
                'messages',
                filter=Q(
                    messages__read_by_client=False,
                    messages__blocked=False,
                    messages__flagged=False,
                    messages__sender__role='artisan'
                )
            )
        ).order_by('-last_message_time')[:5]

        negotiations_data = []
        for negotiation in active_negotiations:
            last_offer = negotiation.messages.filter(
                offer__isnull=False,
                blocked=False,
                flagged=False
            ).order_by('-timestamp').first()

            negotiations_data.append({
                "id": negotiation.id,
                "project_title": negotiation.proposal.project.title,
                "artisan_name": negotiation.proposal.artisan.full_name,
                "unread_messages": negotiation.unread_message_count,
                "last_activity": localtime(negotiation.last_message_time).strftime("%b %d, %H:%M"),
                "initial_price": negotiation.proposal.proposed_price,
                "current_offer": last_offer.offer if last_offer else None,
                "artisan_rating": getattr(negotiation.proposal.artisan, 'rating', 4.5),
            })

        # =========================================================
        # Recent project updates - LIMITED to 2 per project
        # Always show the latest updates (messages, not just milestones)
        # =========================================================
        
        # Get all messages, group by project, take latest 2 per project
        all_messages = ProjectMessage.objects.filter(
            project__client=user,
            blocked=False,
            flagged=False
        ).select_related('project').order_by('-created_at')
        
        # Manually group by project and take only the latest 2 per project
        project_message_counts = {}
        filtered_updates = []
        
        for message in all_messages:
            project_id = message.project.id
            if project_id not in project_message_counts:
                project_message_counts[project_id] = 0
            
            if project_message_counts[project_id] < 2:
                filtered_updates.append(message)
                project_message_counts[project_id] += 1
        
        update_notifications = []
        for update in filtered_updates[:15]:  # Limit to 15 total updates
            has_photo = update.images.exists()
            
            # For the notification message, use the highest progress for the project
            highest_progress = (
                ProjectMessage.objects
                .filter(
                    project=update.project,
                    type='milestone',
                    blocked=False,
                    flagged=False
                )
                .aggregate(max_progress=Max('progress_percentage'))
                .get('max_progress') or 0
            )
            
            # Use the highest progress in the message, not the message's individual progress
            if update.type == 'milestone' and update.progress_percentage:
                # If this is a milestone message, show the highest progress achieved
                message_text = f"Progress update on '{update.project.title}' - {highest_progress}% complete"
            else:
                message_text = f"Update on '{update.project.title}'"
            
            if has_photo:
                message_text += " with new photo(s) 📸"
                
            update_notifications.append({
                "id": update.id,
                "message": message_text,
                "time": localtime(update.created_at).strftime("%b %d, %H:%M"),
                "is_read": update.read_by_client,
                "project_id": update.project.id,
                "project_title": update.project.title,
                "has_photo": has_photo,
                "progress_percentage": highest_progress,  # Include the highest progress
            })

        # Recent proposals notifications
        recent_proposals = Proposal.objects.filter(
            project__client=user
        ).select_related('artisan', 'project').order_by('-created_at')[:5]

        proposal_notifications = []
        for proposal in recent_proposals:
            if not proposal.project.proposals.filter(is_selected=True).exists():
                proposal_notifications.append({
                    "id": proposal.id,
                    "message": f"New proposal for '{proposal.project.title}' from {proposal.artisan.full_name}",
                    "time": localtime(proposal.created_at).strftime("%b %d, %H:%M"),
                    "project_id": proposal.project.id,
                    "artisan_name": proposal.artisan.full_name,
                    "proposed_price": float(proposal.proposed_price),
                    "completion_date": proposal.proposed_date_of_completion,
                })

        dashboard_data = {
            "client_name": user.full_name,
            "completed_projects": completed_projects,
            "ongoing_projects": ongoing_projects,
            "open_projects": open_projects,
            "total_proposals": total_proposals_count,
            # "total_unread_updates": total_unread_updates,
            # "unread_negotiations_count": unread_negotiation_messages_count,
            "combined_unread_negotiation_and_updates": total_unread_updates + unread_negotiation_messages_count,
            "projects_proposals": projects_data,
            "ongoing_projects_data": ongoing_projects_data,
            "active_negotiations": negotiations_data,
            "update_notifications": update_notifications,
            "proposal_notifications": proposal_notifications,
        }

        return Response(dashboard_data)



class ArtisanDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "artisan":
            return Response({"detail": "Access denied."}, status=403)

        # -------------------------------------------------
        # Stats
        # -------------------------------------------------
        proposals_submitted = Proposal.objects.filter(artisan=user).count()
        accepted_proposals = Proposal.objects.filter(artisan=user, is_selected=True)
        ongoing_projects = ProjectRequest.objects.filter(
            proposals__in=accepted_proposals,
            status="in-progress"
        ).distinct()
        completed_projects = ProjectRequest.objects.filter(
            proposals__in=accepted_proposals,
            status="completed"
        ).distinct()
        open_projects_count = ProjectRequest.objects.filter(status="open").count()

        # -------------------------------------------------
        # Ongoing projects with progress & unread updates
        # -------------------------------------------------
        ongoing_projects_data = []
        total_unread_updates = 0

        for project in ongoing_projects:
            # Progress: latest milestone or max milestone
            progress = (
                ProjectMessage.objects
                .filter(
                    project=project,
                    type='milestone',
                    blocked=False,
                    flagged=False
                )
                .aggregate(p=Max('progress_percentage'))
                .get('p') or 0
            )

          


            # Unread updates for artisan
            unread_updates = project.messages.filter(
                read_by_artisan=False,
                blocked=False,
                flagged=False
            ).exclude(sender=user).count()
            total_unread_updates += unread_updates

            ongoing_projects_data.append({
                "id": project.id,
                "title": project.title,
                "progress": progress,
                "deadline": project.deadline,
                "client_name": project.client.full_name,
            })

        # -------------------------------------------------
        # Pending requests (open projects without proposals from artisan)
        # -------------------------------------------------
        pending_requests = ProjectRequest.objects.filter(
            status="open"
        ).exclude(proposals__artisan=user).order_by("deadline")[:5]

        pending_data = [
            {
                "id": req.id,
                "title": req.title,
                "client": req.client.full_name,
                "deadline": req.deadline,
                "description": req.description,
                "budget": req.budget,
            }
            for req in pending_requests
        ]

        # -------------------------------------------------
        # Unread negotiation messages
        # -------------------------------------------------
        unread_negotiation_messages_count = NegotiationMessage.objects.filter(
            negotiation__proposal__artisan=user,
            read_by_artisan=False,
            sender__role='client',
            blocked=False,
            flagged=False,
        ).count()

        # -------------------------------------------------
        # Active negotiations
        # -------------------------------------------------
        active_negotiations = Negotiation.objects.filter(
            proposal__artisan=user,
         
        ).annotate(
            unread_message_count=Count(
                'messages',
                filter=Q(
                    messages__read_by_artisan=False,
                    messages__sender__role='client',
                    messages__blocked=False,
                    messages__flagged=False
                )
            )
        ).order_by('-last_message_time')[:5]

        negotiations_data = []
        for negotiation in active_negotiations:
            last_client_message = negotiation.messages.filter(sender__role='client').order_by('-timestamp').first()
            last_offer = negotiation.messages.filter(offer__isnull=False).order_by('-timestamp').first()

            negotiations_data.append({
                "id": negotiation.id,
                "project_title": negotiation.proposal.project.title,
                "client_name": negotiation.proposal.project.client.full_name,
                "unread_messages": negotiation.unread_message_count,
                "last_activity": localtime(negotiation.last_message_time).strftime("%b %d, %H:%M") if negotiation.last_message_time else None,
                "initial_price": negotiation.proposal.proposed_price,
                "current_offer": last_offer.offer if last_offer else None,
                "last_client_message": last_client_message.message[:100] + "..." if last_client_message else None,
                "has_unread": negotiation.unread_message_count > 0,
            })

        # -------------------------------------------------
        # Final dashboard data
        # -------------------------------------------------
        dashboard_data = {
            "artisan_name": user.full_name,
            "proposals_submitted": proposals_submitted,
            "ongoing_projects_count": ongoing_projects.count(),
            "completed_projects_count": completed_projects.count(),
            "open_projects": open_projects_count,
            "total_unread_updates": total_unread_updates,
            "unread_negotiations_count": unread_negotiation_messages_count,
            "total_notifications": total_unread_updates + unread_negotiation_messages_count,
            "ongoing_projects": ongoing_projects_data,
            "pending_requests": pending_data,
            "active_negotiations": negotiations_data,
        }

        return Response(dashboard_data)



class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "admin":
            return Response({"detail": "Access denied."}, status=403)

        # Total Users
        total_users = User.objects.count()

        # Count by role
        artisans_count = User.objects.filter(role='artisan').count()
        clients_count = User.objects.filter(role='client').count()
        # admins_count = User.objects.filter(role='admin').count()

        # Count by status (using is_active because User has NO 'status' field)
        # active_count = User.objects.filter(is_active=True).count()
        inactive_count = User.objects.filter(is_active=False,role="artisan").count()

        # Projects
        projects = ProjectRequest.objects.all()
        total_projects = projects.count()
        open_projects = projects.filter(status="open").count()
        ongoing_projects = projects.filter(status="in-progress").count()
        completed_projects = projects.filter(status="completed").count()

        dashboard_data = {
            # Users
            "total_users": total_users,
            "artisans": artisans_count,
            "clients": clients_count,
            # "admins": admins_count,

            # User status counts
            # "active_users": active_count,
            "inactive_users": inactive_count,

            # Projects
            "total_projects": total_projects,
            "open_projects": open_projects,
            "ongoing_projects": ongoing_projects,
            "completed_projects": completed_projects,
        }

        return Response(dashboard_data)



class ProjectsManagementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "admin":
            return Response({"detail": "Access denied."}, status=403)

        projects = ProjectRequest.objects.all()

        total_projects = projects.count()
        open_projects = projects.filter(status="open").count()
        active_projects = projects.filter(status="in-progress").count()
        completed_projects = projects.filter(status="completed").count()

        projects_list = []

        
        for project in projects:
        # Count proposals for this specific project
            project_proposals_count = Proposal.objects.filter(project=project).count()
            
            negotiation = Negotiation.objects.filter(proposal__project=project).first()
            agreed_amount = negotiation.final_agreed_amount if negotiation else None

            # Get latest progress percentage (milestone updates only)
            latest_progress_message = ProjectMessage.objects.filter(
                project=project,
                type='milestone'
            ).order_by('-created_at').last()
            progress_percentage = latest_progress_message.progress_percentage if latest_progress_message else 0

            # Get images
            project_images = ProjectImage.objects.filter(request=project)
            images_serialized = ProjectImageSerializer(project_images, many=True, context={'request': request}).data

            projects_list.append({
                "id": project.id,
                "title": project.title,
                "location": project.location,
                "deadline": project.deadline,
                "client": project.client.full_name,
                "description": project.description,
                "budget": project.budget,
                "status": project.status,
                "created_at": project.created_at,
                "proposal_count": project_proposals_count,
                "progress": progress_percentage,
                "images": images_serialized,  # <— include images here
                "artisan": project.artisan.full_name if project.artisan else "Unassigned",
                "agreed_amount":agreed_amount
            })
        
        
        projectManagementData = {
            "total_projects": total_projects,
            "open_projects": open_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "projects": projects_list,
        }


        return Response(projectManagementData)


# ready made products views

class ReadyMadeProductsListCreateView(generics.ListCreateAPIView):
    serializer_class = ReadyMadeProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReadyMadeProduct.objects.filter(
            artisan=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        product = serializer.save(artisan=self.request.user)

        # Handle uploaded images
        request_files = self.request.FILES.getlist("images")  # matches your React FormData key
        for image_file in request_files:
            ProductImage.objects.create(product=product, image=image_file)
  
  



class ReadyMadeProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReadyMadeProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReadyMadeProduct.objects.filter(artisan=self.request.user)

    def perform_update(self, serializer):
        # Save the updated instance first
        instance = serializer.save()

        # Automatically set is_available based on stock
        if instance.stock <= 0:
            instance.is_available = False
        else:
            instance.is_available = True

        instance.save()

            



class ClientReadyProductsListView(generics.ListAPIView):
    serializer_class = ReadyMadeProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReadyMadeProduct.objects.filter(is_available=True).order_by("-created_at")
    
    
    
    
    
    
# =====================================================
# ARTISAN: LIST MATCHED PROJECTS
# =====================================================
# lists to the artisan all projects that were matched to them, along with the match status (pending, viewed, proposed, rejected)
class ArtisanMatchedProjectsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ArtisanMatchedProjectSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role != "artisan":
            return ArtisanMatch.objects.none()

        # Negotiated final amount
        negotiation_qs = Negotiation.objects.filter(
            proposal__project=OuterRef("project__pk"),
            proposal__artisan=user,
            final_agreed_amount__isnull=False,
        ).values("final_agreed_amount")[:1]

        # Selected proposal price fallback
        selected_proposal_qs = Proposal.objects.filter(
            project=OuterRef("project__pk"),
            artisan=user,
            is_selected=True,
        ).values("proposed_price")[:1]

        return (
            ArtisanMatch.objects
            .filter(artisan=user)
            .select_related("project", "project__client")
            .annotate(
                negotiated_cost=Subquery(
                    negotiation_qs,
                    output_field=DecimalField()
                ),
                selected_proposal_price=Subquery(
                    selected_proposal_qs,
                    output_field=DecimalField()
                ),
                agreed_cost=Case(
                    When(
                        negotiated_cost__isnull=False,
                        then=F("negotiated_cost")
                    ),
                    When(
                        selected_proposal_price__isnull=False,
                        then=F("selected_proposal_price")
                    ),
                    default=Value(None),
                    output_field=DecimalField()
                )
            )
            .order_by("-matched_at")
        )


# =====================================================
# ARTISAN: MARK MATCH AS VIEWED
# =====================================================

class MarkMatchedProjectViewedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, match_id):

        match = get_object_or_404(
            ArtisanMatch,
            id=match_id,
            artisan=request.user
        )

        if match.status == "pending":

            match.status = "viewed"
            match.save()

            # Notify client
            try:
                send_push_to_user(
                    user=match.project.client,
                    title="👀 Artisan Viewed Your Project",
                    body=f"{request.user.full_name} viewed your project '{match.project.title}'",
                    data={
                        "type": "match_viewed",
                        "project_id": match.project.id,
                        "artisan_name": request.user.full_name,
                        "url": "/my-requests"
                    }
                )

            except Exception as e:
                print(f"Notification Error: {e}")

            return Response({
                "message": "Match marked as viewed"
            })

        return Response({
            "message": "Match already viewed or responded"
        }, status=400)


# =====================================================
# ARTISAN: ACCEPT / REJECT MATCH
# =====================================================

class RespondToMatchedProjectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, match_id):

        action = request.data.get("action")

        if action not in ["accept", "reject"]:
            return Response({
                "error": "Invalid action"
            }, status=400)

        match = get_object_or_404(
            ArtisanMatch,
            id=match_id,
            artisan=request.user
        )

        if action == "accept":

            match.status = "proposed"

            try:
                send_push_to_user(
                    user=match.project.client,
                    title="✅ Artisan Interested in Your Project",
                    body=f"{request.user.full_name} is interested in '{match.project.title}'",
                    data={
                        "type": "match_accepted",
                        "project_id": match.project.id,
                        "artisan_id": request.user.id,
                        "artisan_name": request.user.full_name,
                        "url": "/my-requests"
                    }
                )

            except Exception as e:
                print(f"Notification Error: {e}")

            message = "Project accepted"

        else:

            match.status = "rejected"
            message = "Project rejected"

        match.save()

        return Response({
            "message": message,
            "status": match.status
        })


# =====================================================
# CLIENT: VIEW MATCHED ARTISANS
# =====================================================

class ProjectMatchedArtisansView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(
            ProjectRequest,
            id=project_id,
            client=self.request.user
        )

        matches = ArtisanMatch.objects.filter(
            project=project
        ).select_related("artisan")

        # ✅ Check for proposals - don't use 'status' field since it doesn't exist
        artisan_ids = [match.artisan.id for match in matches]
        proposals = Proposal.objects.filter(
            project=project,
            artisan_id__in=artisan_ids
        ).values('artisan_id', 'id', 'is_selected')  # ✅ Use is_selected instead of status

        proposal_lookup = {
            p['artisan_id']: {
                'has_proposal': True,
                'proposal_id': p['id'],
                'is_selected': p['is_selected']  # ✅ Track if proposal is selected
            }
            for p in proposals
        }

        data = []
        for match in matches:
            try:
                artisan_profile = ArtisanProfile.objects.get(user=match.artisan)
                tier = artisan_profile.tier
                completed_projects = getattr(artisan_profile, "completed_projects", 0)
                average_rating = getattr(artisan_profile, "average_rating", None)
                bio = getattr(artisan_profile, "bio", "")
                experience_years = getattr(artisan_profile, "experience_years", 0)
                response_rate = getattr(artisan_profile, "response_rate", 0)
            except ArtisanProfile.DoesNotExist:
                tier = "bronze"
                completed_projects = 0
                average_rating = None
                bio = "Skilled artisan ready to work on your project."
                experience_years = 0
                response_rate = 0

            proposal_info = proposal_lookup.get(match.artisan.id, {
                'has_proposal': False,
                'proposal_id': None,
                'is_selected': False
            })

            data.append({
                "id": match.id,
                "artisan_id": match.artisan.id,
                "artisan_name": match.artisan.full_name,
                "artisan_email": match.artisan.email,
                "tier": tier,
                "average_rating": average_rating,
                "completed_projects": completed_projects,
                "bio": bio,
                "experience_years": experience_years,
                "response_rate": response_rate,
                "status": match.project.status,  # This is project status, not proposal status
                "matched_at": match.matched_at,
                "project_id": match.project.id,
                "project_title": match.project.title,
                "budget": match.project.budget,
                # ✅ Proposal info without status field
                "has_proposal": proposal_info['has_proposal'],
                "proposal_id": proposal_info['proposal_id'],
                "proposal_selected": proposal_info['is_selected'],  # Track if selected
            })

        return Response(data)   
    
    
    
    
class ArtisanProjectDetailView(generics.RetrieveAPIView):
    serializer_class = ProjectRequestBaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Artisan can only view projects where they have a selected (accepted) proposal
        return ProjectRequest.objects.filter(
            proposals__artisan=self.request.user,
            proposals__is_selected=True
        ).distinct()