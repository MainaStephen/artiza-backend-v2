# negotiations/serializers.py
from rest_framework import serializers
from .models import Negotiation, NegotiationMessage
from proposals.serializers import ProposalSerializer

class NegotiationMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.full_name')
    sender_role = serializers.ReadOnlyField(source='sender.role')
    is_unread = serializers.SerializerMethodField()

    class Meta:
        model = NegotiationMessage
        fields = [
            'id', 'negotiation', 'sender', 'sender_name', 'sender_role',
            'message', 'offer', 'is_accepted', 'timestamp',
            'read_by_client', 'read_by_artisan', 'is_unread'
        ]
        read_only_fields = ['negotiation', 'sender', 'timestamp']

    def get_is_unread(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        user = request.user
        if user.role == 'client':
            return not obj.read_by_client and obj.sender != user
        elif user.role == 'artisan':
            return not obj.read_by_artisan and obj.sender != user
        return False

class NegotiationSerializer(serializers.ModelSerializer):
    messages = NegotiationMessageSerializer(many=True, read_only=True)
    proposal_details = ProposalSerializer(source='proposal', read_only=True)
    artisan_name = serializers.ReadOnlyField(source='proposal.artisan.full_name')
    client_name = serializers.ReadOnlyField(source='proposal.project.client.full_name')
    project_title = serializers.ReadOnlyField(source='proposal.project.title')
    unread_count = serializers.SerializerMethodField()
    has_unread = serializers.SerializerMethodField()

    class Meta:
        model = Negotiation
        fields = [
            'id', 'proposal', 'proposal_details', 'artisan_name', 'client_name', 'project_title',
            'pending_final_amount', 'final_agreed_amount', 'is_closed', 'created_at', 'messages',  # Changed from pending_final_offer
            'has_unread_client', 'has_unread_artisan', 'unread_count', 'has_unread'
        ]
        read_only_fields = ['created_at']

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        
        user = request.user
        if user.role == 'client':
            return obj.messages.filter(read_by_client=False).exclude(sender=user).count()
        elif user.role == 'artisan':
            return obj.messages.filter(read_by_artisan=False).exclude(sender=user).count()
        return 0

    def get_has_unread(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        user = request.user
        if user.role == 'client':
            return obj.has_unread_client
        elif user.role == 'artisan':
            return obj.has_unread_artisan
        return False