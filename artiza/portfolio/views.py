# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.db.models import Sum, OuterRef, Subquery
# from projects.models import ProjectRequest
# from reviews.models import Rating
# from .models import PortfolioItem
# from .serializers import PortfolioItemSerializer
# from users.models import User


# def get_artisan_avatar(user, request=None):
#     """Return absolute URL for artisan avatar or fallback."""
#     if user.profile_picture and hasattr(user.profile_picture, 'url') and user.profile_picture.name:
#         return request.build_absolute_uri(user.profile_picture.url) if request else user.profile_picture.url

#     full_name = user.full_name or "User"
#     return f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=673200&color=fff&size=200"


# class ArtisanPortfolioView(APIView):
#     def get(self, request, *args, **kwargs):
#         artisan_id = kwargs.get("artisan_id")

#         # Fetch artisan
#         try:
#             artisan = User.objects.get(id=artisan_id, role="artisan")
#         except User.DoesNotExist:
#             return Response({"detail": "Artisan not found"}, status=404)

#         # Completed projects
#         completed_projects = ProjectRequest.objects.filter(
#             artisan=artisan,
#             status="completed"
#         )

#         # Only projects with at least one rating
#         rated_project_ids = Rating.objects.filter(
#             project__in=completed_projects
#         ).values_list("project_id", flat=True).distinct()
#         completed_projects = completed_projects.filter(id__in=rated_project_ids)

#         # Create missing portfolio items
#         for project in completed_projects:
#             if not hasattr(project, "portfolio_item"):
#                 PortfolioItem.objects.create(user=artisan, project_request=project)

#         # Latest rating subquery for each portfolio item
#         latest_rating_subquery = Rating.objects.filter(
#             project_id=OuterRef('project_request_id')
#         ).order_by('-id')

#         # Portfolio items with project_score annotation
#         portfolio_items = PortfolioItem.objects.filter(
#             user=artisan,
#             project_request__in=completed_projects
#         ).prefetch_related("project_request__images").annotate(
#             project_score=Subquery(latest_rating_subquery.values('score')[:1])
#         )

#         # Overall stats
#         projects_completed = completed_projects.count()
#         artisan_ratings = Rating.objects.filter(project__in=completed_projects)
#         total_score = artisan_ratings.aggregate(total=Sum("score"))["total"] or 0
#         rated_project_count = artisan_ratings.values("project").distinct().count()
#         avg_rating = total_score / rated_project_count if rated_project_count else 0

#         first_project = completed_projects.order_by("date_of_completion").first()
#         years_of_experience = (
#             max(0, first_project.date_of_completion.year - artisan.date_joined.year)
#             if first_project and first_project.date_of_completion else 0
#         )

#         # Serialize portfolio items with request context
#         portfolio_data = PortfolioItemSerializer(
#             portfolio_items, many=True, context={'request': request}
#         ).data

#         return Response({
#             "artisan_avatar": get_artisan_avatar(artisan, request),
#             "artisan_name": artisan.full_name,
#             "artisan_id": artisan.id,
#             "years_of_experience": years_of_experience,
#             "client_rating": round(avg_rating, 1),
#             "projects_completed": projects_completed,
#             "portfolio_items": portfolio_data,
#         })





# class MyArtisanPortfolioView(APIView):
#     def get(self, request, *args, **kwargs):
#         artisan = request.user

#         if artisan.role != "artisan":
#             return Response({"detail": "Only artisans can view this resource"}, status=403)

#         # Reuse the same logic by calling the main view’s method
#         view = ArtisanPortfolioView()
#         return view.get(request, artisan_id=artisan.id)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, OuterRef, Subquery
from itertools import chain
from datetime import datetime

from projects.models import ProjectRequest
from reviews.models import Rating
from .models import PortfolioItem, PortfolioProject
from .serializers import UniversalPortfolioSerializer, CreateLegacyPortfolioProjectSerializer
from users.models import User
from .models import PortfolioProject, PortfolioProjectImage


def get_artisan_avatar(user, request=None):
    """Return absolute URL for artisan avatar or fallback."""
    if user.profile_picture and hasattr(user.profile_picture, 'url') and user.profile_picture.name:
        return request.build_absolute_uri(user.profile_picture.url) if request else user.profile_picture.url

    full_name = user.full_name or "User"
    return f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=673200&color=fff&size=200"


class ArtisanPortfolioView(APIView):
    """Unified portfolio view for an artisan with stats and projects."""

    def get(self, request, *args, **kwargs):
        artisan_id = kwargs.get("artisan_id")
        try:
            artisan = User.objects.get(id=artisan_id, role="artisan")
        except User.DoesNotExist:
            return Response({"detail": "Artisan not found"}, status=404)

        # --- PLATFORM PROJECTS ---
        completed_projects = ProjectRequest.objects.filter(artisan=artisan, status="completed")
        rated_project_ids = Rating.objects.filter(project__in=completed_projects).values_list("project_id", flat=True).distinct()
        completed_projects = completed_projects.filter(id__in=rated_project_ids)

        for project in completed_projects:
            if not hasattr(project, "portfolio_item"):
                PortfolioItem.objects.create(user=artisan, project_request=project)

        latest_rating_subquery = Rating.objects.filter(project_id=OuterRef('project_request_id')).order_by('-id')

        platform_portfolio_items = PortfolioItem.objects.filter(
            user=artisan,
            project_request__in=completed_projects
        ).prefetch_related("project_request__ratings__images").annotate(
            project_score=Subquery(latest_rating_subquery.values('score')[:1])
        )

        # --- LEGACY PROJECTS ---
        legacy_projects = PortfolioProject.objects.filter(artisan=artisan).prefetch_related("images")

        all_portfolio_items = list(chain(platform_portfolio_items, legacy_projects))

        for item in all_portfolio_items:
            if hasattr(item, "project_request"):
                item.rating = getattr(item, "project_score", None)
            # Legacy project already has rating

        portfolio_data = UniversalPortfolioSerializer(all_portfolio_items, many=True, context={'request': request}).data

        # --- STATS ---
        projects_completed = completed_projects.count() + legacy_projects.count()
        legacy_projects_count = PortfolioProject.objects.filter(artisan=artisan).count()

        platform_ratings = Rating.objects.filter(project__in=completed_projects).values_list("score", flat=True)
        legacy_ratings = legacy_projects.values_list("rating", flat=True)
        all_ratings = list(platform_ratings) + [r for r in legacy_ratings if r is not None]
        avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0

        # Convert all dates to date objects for comparison
        platform_dates = [d for d in completed_projects.order_by("date_of_completion").values_list("date_of_completion", flat=True) if d is not None]
        legacy_dates = [d.date() if isinstance(d, datetime) else d for d in legacy_projects.order_by("created_at").values_list("created_at", flat=True) if d is not None]
        all_dates = platform_dates + legacy_dates

        if all_dates:
            first_project_date = min(all_dates)
            years_of_experience = max(0, first_project_date.year - artisan.date_joined.year)
        else:
            years_of_experience = 0

        return Response({
            "artisan_avatar": get_artisan_avatar(artisan, request),
            "artisan_name": artisan.full_name,
            "artisan_id": artisan.id,
            "years_of_experience": years_of_experience,
            "client_rating": round(avg_rating, 1),
            "projects_completed": projects_completed,
            "portfolio_items": portfolio_data,
            "legacy_projects_count": legacy_projects_count,
        })


class MyArtisanPortfolioView(APIView):
    """Portfolio view for the authenticated artisan."""

    def get(self, request, *args, **kwargs):
        artisan = request.user
        if artisan.role != "artisan":
            return Response({"detail": "Only artisans can view this resource"}, status=403)

        view = ArtisanPortfolioView()
        return view.get(request, artisan_id=artisan.id)


class CreateLegacyPortfolioProjectView(APIView):
    """API for artisans to add legacy projects to their portfolio."""

    MAX_LEGACY_PROJECTS = 5

    def post(self, request, *args, **kwargs):
        artisan = request.user
        if artisan.role != "artisan":
            return Response(
                {"detail": "Only artisans can create legacy projects"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Count only true legacy projects
        existing_count = PortfolioProject.objects.filter(
            artisan=artisan
        ).values('id').distinct().count()

        if existing_count >= self.MAX_LEGACY_PROJECTS:
            return Response(
                {"detail": f"You can only add up to {self.MAX_LEGACY_PROJECTS} legacy projects"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate input using the serializer
        serializer = CreateLegacyPortfolioProjectSerializer(data=request.data)
        if serializer.is_valid():
            validated = serializer.validated_data

            # Create the legacy project
            project = PortfolioProject.objects.create(
                artisan=artisan,
                title=validated['title'],
                description=validated.get('description', ''),
                rating=validated['rating']
            )

            # Save images
            for img in validated['images']:
                PortfolioProjectImage.objects.create(project=project, image=img)

            remaining_slots = self.MAX_LEGACY_PROJECTS - (existing_count + 1)
            return Response({
                "detail": "Legacy project created successfully",
                "remaining_slots": remaining_slots
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
