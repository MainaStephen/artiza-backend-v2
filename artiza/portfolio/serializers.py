# 
from rest_framework import serializers
from .models import PortfolioItem, PortfolioProject


class PortfolioProjectImageSerializer(serializers.ModelSerializer):
    """Serializer for legacy project images."""
    image = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioProject
        fields = ["id", "image", "uploaded_at"]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and obj.image.name:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


class UniversalPortfolioSerializer(serializers.Serializer):
    """
    Unified serializer for:
      - Platform projects (PortfolioItem)
      - Legacy/pre-platform projects (PortfolioProject)
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    rating = serializers.FloatField(allow_null=True)
    images = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    
        
    def get_images(self, obj):
        request = self.context.get("request")
        images = []

        if hasattr(obj, "project_request") and obj.project_request:
            rating = obj.project_request.ratings.filter(artisan=obj.user).first()
            if rating:
                for img in rating.images.all():
                    if img.image and img.image.name:
                        images.append({
                            "id": img.id,
                            "image": request.build_absolute_uri(img.image.url) if request else img.image.url
                        })

        elif hasattr(obj, "images"):
            for img in obj.images.all():
                if img.image and img.image.name:
                    images.append({
                        "id": img.id,
                        "image": request.build_absolute_uri(img.image.url) if request else img.image.url
                    })

        return images


class ArtisanStatsSerializer(serializers.Serializer):
    """Serializer for artisan portfolio stats."""
    years_of_experience = serializers.IntegerField()
    client_rating = serializers.FloatField()
    projects_completed = serializers.IntegerField()


from rest_framework import serializers
from .models import PortfolioProject, PortfolioProjectImage

class CreateLegacyPortfolioProjectSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, required=False)
    rating = serializers.FloatField(min_value=1, max_value=5)
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False,
        write_only=True
    )
