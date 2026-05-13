from rest_framework import serializers
from .models import Rating, RatingImage

class RatingImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = RatingImage
        fields = ["id", "image", "image_url", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None

class ProductReviewSerializer(serializers.ModelSerializer):
    images = RatingImageSerializer(many=True, read_only=True)
    artisan_name = serializers.CharField(source='artisan.username', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = Rating
        fields = [
            "id", "client", "artisan", "artisan_name", "project", 
            "project_title", "score", "review", "images", "created"
        ]
        read_only_fields = [
            "id", "client", "artisan", "artisan_name", "project", 
            "project_title", "created", "images"
        ]
        
        
class ProductReviewTestimonialsSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    
    # project_title = serializers.CharField(source='project.title', read_only=True)
    # images = RatingImageSerializer(many=True, read_only=True)

    class Meta:
        model = Rating
        fields = [
            "id", 
             "score", "review", "client_name"
        ]
        read_only_fields = [
            "id", "score", "review","client_name"
        ]