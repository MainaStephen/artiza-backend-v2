from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from .models import Rating, RatingImage
from .serializers import ProductReviewSerializer,ProductReviewTestimonialsSerializer
from projects.models import ProjectRequest

class ProductReviewCreateView(generics.CreateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_id")
        if not project_id:
            raise PermissionDenied("Project ID is required in the URL.")

        try:
            project = ProjectRequest.objects.get(id=project_id)
        except ProjectRequest.DoesNotExist:
            raise PermissionDenied("Project does not exist.")

        if project.client != self.request.user:
            raise PermissionDenied("You are not allowed to rate this project.")

        if project.status != "completed":
            raise PermissionDenied("You can only rate completed projects.")

        artisan = project.artisan
        if not artisan:
            raise PermissionDenied("This project has no assigned artisan to rate.")

        # Prevent duplicate rating
        if Rating.objects.filter(client=self.request.user, artisan=artisan, project=project).exists():
            raise PermissionDenied("You have already rated this artisan for this project.")

        # Get data from request
        score = request.data.get('score')
        review = request.data.get('review', '')
        images = request.FILES.getlist('images')

        if not score:
            raise PermissionDenied("Score is required.")

        # Create the rating
        rating = Rating.objects.create(
            client=self.request.user,
            artisan=artisan,
            project=project,
            score=score,
            review=review
        )

        # Handle multiple images
        for image_file in images:
            RatingImage.objects.create(rating=rating, image=image_file)

        # Serialize the response with context for image URLs
        serializer = self.get_serializer(rating, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductReviewRetrieveView(generics.RetrieveAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        project_id = self.kwargs.get("project_id")
        
        try:
            project = ProjectRequest.objects.get(id=project_id)
        except ProjectRequest.DoesNotExist:
            raise NotFound("Project does not exist.")

        if project.client != self.request.user:
            raise PermissionDenied("You are not allowed to view reviews for this project.")

        try:
            # Get rating for this project and user
            rating = Rating.objects.get(project=project, client=self.request.user)
            return rating
        except Rating.DoesNotExist:
            raise NotFound("No rating found for this project.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    
    
class ProductReviewTestimonialsView(generics.ListAPIView):
    serializer_class = ProductReviewTestimonialsSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Rating.objects.all().order_by('-created')  # Latest reviews first

