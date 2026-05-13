from rest_framework import serializers
from .models import ProjectMessage, ProjectMessageImage

class ProjectMessageImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMessageImage
        fields = ["id", "image"]

    def get_image(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url



class ProjectMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source="sender.full_name")
    sender_role = serializers.ReadOnlyField(source="sender.role")
    sender_id = serializers.ReadOnlyField(source="sender.id")

    images = ProjectMessageImageSerializer(many=True, read_only=True)

    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ProjectMessage
        fields = [
            "id",
            "sender_id",
            "project",
            "sender",
            "sender_name",
            "sender_role",
            "type",
            "message",
            "note",
            "progress_percentage",
            "images",
            "uploaded_images",
            "flagged",
            "blocked",
            "reviewed_by_admin",
            "reviewed_at",
            "created_at",
            "read_by_client",
            "read_by_artisan",
        ]
        read_only_fields = [
            "sender",
            "project",
            "images",
            "flagged",
            "blocked",
            "reviewed_by_admin",
            "reviewed_at",
            "created_at",
            "read_by_client",
            "read_by_artisan",
        ]

    # -----------------------
    # FIELD-LEVEL VALIDATION
    # -----------------------
    def validate_progress_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Progress percentage must be between 0 and 100."
            )
        return value

    # -----------------------
    # OBJECT-LEVEL VALIDATION
    # -----------------------
    def validate(self, attrs):
        message_type = attrs.get("type", "chat")
        progress = attrs.get("progress_percentage")
        project = self.context.get("project_instance")

        # Milestone requires progress
        if message_type == "milestone" and progress is None:
            raise serializers.ValidationError({
                "progress_percentage": "Milestone updates require progress percentage."
            })

        # Chat messages cannot update progress
        if message_type == "chat" and progress not in (None, 0):
            raise serializers.ValidationError({
                "progress_percentage": "Chat messages cannot update progress."
            })

        # Progress cannot decrease
        if progress is not None and project:
            latest = ProjectMessage.objects.filter(
                project=project,
                type="milestone",
                blocked=False,
            ).order_by("-created_at").first()

            if latest and progress < latest.progress_percentage:
                raise serializers.ValidationError({
                    "progress_percentage": (
                        f"Progress cannot decrease. "
                        f"Last progress was {latest.progress_percentage}%."
                    )
                })

        return attrs

    # -----------------------
    # CREATE
    # -----------------------
    def create(self, validated_data):
        images = validated_data.pop("uploaded_images", [])
        request = self.context.get("request")

        if request:
            user = request.user
            validated_data["sender"] = user

            # Mark sender's own message as read
            if user.role == "client":
                validated_data["read_by_client"] = True
                validated_data["read_by_artisan"] = False
            elif user.role == "artisan":
                validated_data["read_by_client"] = False
                validated_data["read_by_artisan"] = True
            else:
                validated_data["read_by_client"] = False
                validated_data["read_by_artisan"] = False

        message = ProjectMessage.objects.create(**validated_data)

        for img in images:
            ProjectMessageImage.objects.create(
                message=message,
                image=img,
            )

        return message

# -------------------------
# Admin: Flagged Messages List
# -------------------------
class FlaggedMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source="sender.full_name")
    images = ProjectMessageImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectMessage
        fields = [
            "id",
            "project",
            "sender",
            "sender_name",
            "message",
            "note",
            "progress_percentage",
            "images",
            "flagged",
            "blocked",
            "reviewed_by_admin",
            "reviewed_at",
            "created_at",
        ]


# -------------------------
# Admin: Review a Flagged Message
# -------------------------
class ReviewFlaggedMessageSerializer(serializers.Serializer):
    review_message = serializers.CharField(required=False, allow_blank=True)
    unblock = serializers.BooleanField(required=False, default=False)