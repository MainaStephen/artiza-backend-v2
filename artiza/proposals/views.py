# views.py
from rest_framework import generics, permissions,serializers
from .models import Proposal
from .serializers import ProposalSerializer,ProposalWithProjectImagesSerializer
from projects.models import ProjectRequest
from rest_framework.response import Response



class ProposalCreateView(generics.CreateAPIView):
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        project_id = self.request.data.get("project")
        user = self.request.user

        if not project_id:
            raise serializers.ValidationError({"project": "This field is required."})

        try:
            project = ProjectRequest.objects.get(id=project_id)
        except ProjectRequest.DoesNotExist:
            raise serializers.ValidationError({"project": "Invalid project ID."})

        # ✅ Check if artisan already has a proposal for this project
        existing_proposal = Proposal.objects.filter(
            artisan=user, project=project
        ).exists()

        if existing_proposal:
            raise serializers.ValidationError(
                {"detail": "You have already submitted a proposal for this project."}
            )

        # ✅ Otherwise, save normally
        serializer.save(artisan=user, project=project)




class ProposalListView(generics.ListAPIView):
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        if project_id:
            return Proposal.objects.filter(project_id=project_id).order_by('-created_at')
        return Proposal.objects.none()
    
    



class ProposalSelectView(generics.UpdateAPIView):
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Proposal.objects.all()
    lookup_field = 'id'

    def patch(self, request, *args, **kwargs):
        proposal = self.get_object()
        project = proposal.project
        user = request.user
        # Only the client who owns the project can select a proposal
        if project.client != user:
            return Response({"detail": "Not allowed"}, status=403)

        # Unselect all other proposals for this project
        Proposal.objects.filter(project=project).update(is_selected=False)

        # Select this proposal
        proposal.is_selected = True
        proposal.save()

        project.artisan = proposal.artisan

        if project.status == "open":
            project.status = "in-progress"

        project.save()

        serializer = self.get_serializer(proposal)
        return Response(serializer.data)


class ListArtisanProposals(generics.ListAPIView):
    serializer_class = ProposalWithProjectImagesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Filter proposals where the artisan is the logged-in user
        return Proposal.objects.filter(artisan=user).order_by('-created_at')
    
    
class ProposalDetailView(generics.RetrieveAPIView):
    """Fetch detailed proposal information"""
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Proposal.objects.all()
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        proposal = self.get_object()
        project = proposal.project
        
        # Check permissions: artisan can view own proposals, client can view proposals for their project
        if request.user != proposal.artisan and request.user != project.client:
            return Response(
                {"detail": "You don't have permission to view this proposal"},
                status=403
            )
        
        serializer = self.get_serializer(proposal)
        return Response(serializer.data)
        