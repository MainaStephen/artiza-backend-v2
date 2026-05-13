# proposals/serializers.py
from rest_framework import serializers
from .models import Proposal
from projects.models import ProjectImage

class ProposalSerializer(serializers.ModelSerializer):
    artisan_username = serializers.ReadOnlyField(source='artisan.full_name')
    project_title = serializers.ReadOnlyField(source='project.title')
    # final_price = serializers.ReadOnlyField()  # ✅ Add computed final price

    class Meta:
        model = Proposal
        fields = [
            'id',
            'project',
            'project_title',
            'artisan',
            'artisan_username',
            'proposed_price',
            'negotiated_price',  # ✅ Add negotiated price field
            # 'final_price',       # ✅ Add computed final price
            'proposed_date_of_completion',
            'note',
            'is_selected',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'artisan', 'project', 'is_selected', 'created_at', 'updated_at'
        ]

class ProjectImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectImage
        fields = ['id', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

class ProposalWithProjectImagesSerializer(serializers.ModelSerializer):
    artisan_username = serializers.ReadOnlyField(source='artisan.full_name')
    project_title = serializers.ReadOnlyField(source='project.title')
    project_images = serializers.SerializerMethodField()
    client_username = serializers.ReadOnlyField(source='project.client.full_name')
    project_description = serializers.ReadOnlyField(source='project.description')
    status = serializers.SerializerMethodField()

    has_negotiation = serializers.SerializerMethodField()  
    negotiated_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True) 
    project_budget = serializers.ReadOnlyField(source='project.budget')
    class Meta:
        model = Proposal
        fields = [
            'id',
            'project',
            'project_title',
            'project_images',
            'artisan',
            'artisan_username',
            'proposed_price',
            'negotiated_price',  # ✅ Add negotiated price
            # 'final_price',       # ✅ Add computed final price
            'has_negotiation',   # ✅ Add negotiation check
            'proposed_date_of_completion',
            'note',
            'is_selected',
            'status',
            'created_at',
            'updated_at',
            'client_username',
            'project_description',
            'project_budget',
        ]
        read_only_fields = [
            'artisan', 'project', 'is_selected', 'status', 'created_at', 
            'updated_at', 'project_description', 'client_username','project_budget'
        ]
    

    def get_project_images(self, obj):
        images = obj.project.images.all()
        request = self.context.get('request')
        return [
            request.build_absolute_uri(img.image.url) if request else img.image.url
            for img in images
        ]

    def get_status(self, obj):
        """
        Compute status dynamically:
        - Accepted: is_selected=True
        - Declined: is_selected=False and some other proposal is selected for this project
        - Pending: no proposal selected yet
        """
        if obj.is_selected:
            return "Accepted"
        elif obj.project.proposals.filter(is_selected=True).exists():
            return "Declined"
        else:
            return "Pending"

    def get_has_negotiation(self, obj):
        """
        Check if this proposal has an associated negotiation
        """
        return hasattr(obj, 'negotiation') and obj.negotiation is not None
    
