from django.contrib import admin
from .models import Negotiation, NegotiationMessage


class NegotiationMessageInline(admin.TabularInline):
    model = NegotiationMessage
    extra = 1
    fields = ("sender", "message", "offer", "timestamp", "is_accepted")
    readonly_fields = ("timestamp",)


@admin.register(Negotiation)
class NegotiationAdmin(admin.ModelAdmin):
    list_display = ("id","proposal","pending_final_amount", "final_agreed_amount", "is_closed", "created_at")
    list_filter = ("is_closed", "created_at")
    search_fields = ("proposal__project__title", "proposal__user__email")
    inlines = [NegotiationMessageInline]
    readonly_fields = ("created_at",)


@admin.register(NegotiationMessage)
class NegotiationMessageAdmin(admin.ModelAdmin):
    list_display = ("id","negotiation", "sender", "short_message", "offer", "timestamp", "is_accepted")
    list_filter = ("is_accepted", "timestamp")
    search_fields = ("negotiation__proposal__project__title", "sender__email", "message")
    readonly_fields = ("timestamp",)

    def short_message(self, obj):
        return obj.message[:40] + ("..." if len(obj.message) > 40 else "")
    short_message.short_description = "Message"
