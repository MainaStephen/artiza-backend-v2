from rest_framework import serializers
from .models import ProjectRequest, ProjectImage , ReadyMadeProduct, ProductImage
from django.conf import settings


class ProjectImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectImage
        fields = ["id", "image", "uploaded_at", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            
            if request:
                return request.build_absolute_uri(obj.image.url)
            # Otherwise fallback to settings.MEDIA_URL
            return f"{settings.MEDIA_URL}{obj.image}"
        return None


# Base serializer for shared fields
class ProjectRequestBaseSerializer(serializers.ModelSerializer):
    images = ProjectImageSerializer(many=True, read_only=True)
    client = serializers.CharField(source="client.full_name", read_only=True)
    progress = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ProjectRequest
        fields = [
            "id", "client", "title", "description", "budget", "location",
            "deadline", "status", "created_at", "updated_at", "images","date_of_completion","progress",
        ]
        read_only_fields = ["client", "status", "created_at", "updated_at","date_of_completion","progress"]




class ProjectRequestOpenSerializer(ProjectRequestBaseSerializer):
    has_proposal = serializers.BooleanField(read_only=True)
    proposal_date = serializers.DateTimeField(read_only=True, allow_null=True)
    proposed_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        allow_null=True
    )

    class Meta(ProjectRequestBaseSerializer.Meta):
        fields = ProjectRequestBaseSerializer.Meta.fields + [
            "has_proposal",
            "proposal_date",
            "proposed_price",
        ]


# Serializer for client projects with updates (explicit fields)
class ProjectRequestClientUpdatesSerializer(ProjectRequestBaseSerializer):
    unread_updates_count = serializers.IntegerField(read_only=True)
    progress = serializers.IntegerField(read_only=True)
    last_update_time = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = ProjectRequest
        fields = [
            "id", "client", "title", "description", "budget", "location",
            "deadline", "status", "created_at", "updated_at", "images",
            "unread_updates_count", "last_update_time","progress"
        ]
        read_only_fields = ["client", "status", "created_at", "updated_at", "unread_updates_count","progress"]


# Serializer for creating/updating projects with image uploads (explicit fields)
class ProjectRequestCreateSerializer(ProjectRequestBaseSerializer):
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False,
        help_text="Upload multiple images"
    )

    class Meta:
        model = ProjectRequest
        fields = [
            "id", "client", "title", "description", "budget", "location",
            "deadline", "status", "created_at", "updated_at", "images",
            "uploaded_images"
        ]
        read_only_fields = ["client", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        project_request = ProjectRequest.objects.create(**validated_data)

        for img in uploaded_images:
            ProjectImage.objects.create(request=project_request, image=img)

        return project_request


# In your serializers.py
class ClientProjectRequestSerializer(ProjectRequestBaseSerializer):
    proposals_count = serializers.IntegerField(read_only=True)
    agreed_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    unread_negotiation_messages = serializers.IntegerField(read_only=True)  # Add this line

    class Meta(ProjectRequestBaseSerializer.Meta):
        fields = ProjectRequestBaseSerializer.Meta.fields + [
            'proposals_count', 
            'agreed_cost',
            'unread_negotiation_messages' 
        ]
# In your serializers.py

class ArtisanAcceptedProjectsSerializer(ProjectRequestBaseSerializer):
    unread_updates = serializers.IntegerField(read_only=True)

    class Meta(ProjectRequestBaseSerializer.Meta):
        fields = ProjectRequestBaseSerializer.Meta.fields + [
            'unread_updates', 
           
        ]
        




class ReadyMadeProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "uploaded_at", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")

        if not obj.image:
            return None

        if request:
            return request.build_absolute_uri(obj.image.url)

        return f"{settings.MEDIA_URL}{obj.image.name}"


        
class ReadyMadeProductSerializer(serializers.ModelSerializer):
    images = ReadyMadeProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ReadyMadeProduct
        fields = [
            "id",
            "name",
            "description",
            "category",
            "price",
            "created_at",
            "updated_at",
            "images",
            "is_available",
            "stock"
        ]

from artisanmatching.models import ArtisanMatch


# =====================================================
# ARTISAN MATCHED PROJECTS SERIALIZER
# =====================================================

class ArtisanMatchedProjectSerializer(serializers.ModelSerializer):

    project_title = serializers.CharField(
        source="project.title",
        read_only=True
    )

    description = serializers.CharField(
        source="project.description",
        read_only=True
    )

    budget = serializers.DecimalField(
        source="project.budget",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    location = serializers.CharField(
        source="project.location",
        read_only=True
    )

    deadline = serializers.DateField(
        source="project.deadline",
        read_only=True
    )

    client_name = serializers.CharField(
        source="project.client.full_name",
        read_only=True
    )
    
    images = ProjectImageSerializer(
    source="project.images",
    many=True,
    read_only=True
    )
    
    status = serializers.CharField(
        source="project.status",
        read_only=True
    )
    

    class Meta:
        model = ArtisanMatch
        fields = [
            "id",
            "project",
            "project_title",
            "description",
            "budget",
            "location",
            "deadline",
            "client_name",
            "status",
            "matched_at",
            "images",
        ]


# =====================================================
# CLIENT VIEW MATCHED ARTISANS SERIALIZER
# =====================================================

class ProjectMatchedArtisanSerializer(serializers.ModelSerializer):

    artisan_id = serializers.IntegerField(
        source="artisan.id",
        read_only=True
    )

    artisan_name = serializers.CharField(
        source="artisan.full_name",
        read_only=True
    )

    artisan_email = serializers.CharField(
        source="artisan.email",
        read_only=True
    )

    project_id = serializers.IntegerField(
        source="project.id",
        read_only=True
    )

    project_title = serializers.CharField(
        source="project.title",
        read_only=True
    )

    budget = serializers.DecimalField(
        source="project.budget",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    status = serializers.CharField(
        source="project.status",
        read_only=True
    )

    class Meta:
        model = ArtisanMatch
        fields = [
            "id",
            "artisan_id",
            "artisan_name",
            "artisan_email",
            "project_id",
            "project_title",
            "budget",
            "status",
            "matched_at",
        ]
        
        
        