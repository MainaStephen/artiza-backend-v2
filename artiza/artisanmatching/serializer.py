from rest_framework import serializers
from .models import ArtisanMatch


class ArtisanMatchSerializer(serializers.ModelSerializer):

    project_title = serializers.CharField(source="project.title", read_only=True)
    budget = serializers.DecimalField(source="project.budget", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ArtisanMatch
        fields = [
            "id",
            "project",
            "project_title",
            "budget",
            "status",
            "matched_at",
        ]