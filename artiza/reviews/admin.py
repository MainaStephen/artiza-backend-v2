from django.contrib import admin
from .models import Rating, RatingImage

# Inline for RatingImage
class RatingImageInline(admin.TabularInline):
    model = RatingImage
    extra = 1
    readonly_fields = ('uploaded_at',)
    fields = ('image', 'uploaded_at')

# Admin for Rating
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'artisan', 'project', 'score', 'created')
    list_filter = ('score', 'created', 'project')
    search_fields = ('client__username', 'artisan__username', 'project__title', 'review')
    readonly_fields = ('created',)
    inlines = [RatingImageInline]

# Admin for RatingImage (optional, usually managed via inline)
@admin.register(RatingImage)
class RatingImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'rating', 'image', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    search_fields = ('rating__project__title', 'rating__client__username', 'rating__artisan__username')
