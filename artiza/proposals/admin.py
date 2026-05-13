from django.contrib import admin
from .models import Proposal

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    # Columns to display in the admin list view
    list_display = (
        'id',
        'project',
        'get_project_title',
        'artisan',
        'get_artisan_full_name',
        'proposed_price',
        'proposed_date_of_completion',
        'is_selected',
        'created_at',
        'updated_at',
    )

    # Fields you can filter by in the sidebar
    list_filter = ('is_selected', 'created_at', 'updated_at')

    # Fields you can search by
    search_fields = ('project__title', 'artisan__full_name', 'note')

    # Fields that are read-only in the admin form
    readonly_fields = ('created_at', 'updated_at', 'get_artisan_full_name', 'get_project_title')

    # Optional: ordering by newest first
    ordering = ('-created_at',)

    # Optional: collapse fields
    fieldsets = (
        (None, {
            'fields': (
                'project',
                'get_project_title',
                'artisan',
                'get_artisan_full_name',
                'proposed_price',
                'proposed_date_of_completion',
                'note',
                'is_selected',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ✅ Methods to show related fields
    def get_artisan_full_name(self, obj):
        return obj.artisan.full_name
    get_artisan_full_name.short_description = 'Artisan full Name'

    def get_project_title(self, obj):
        return obj.project.title
    get_project_title.short_description = 'Project Title'
