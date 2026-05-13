from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/proposals/', include('proposals.urls')),
    path('api/updates/', include('updates.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/portfolio/', include('portfolio.urls')),
    path('api/negotiations/', include('negotiations.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/checkout/', include('checkout.urls')),
    path('api/artisan-matches/', include('artisanmatching.urls')),
]

if settings.DEBUG:
   
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

