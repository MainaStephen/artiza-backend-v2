from django.urls import path
from .views import ArtisanPortfolioView,MyArtisanPortfolioView,CreateLegacyPortfolioProjectView

urlpatterns = [
    path('artisan-portfolio/', MyArtisanPortfolioView.as_view(), name='artisan-portfolio'),
    path('artisan-portfolio/<int:artisan_id>/', ArtisanPortfolioView.as_view(), name='artisan-portfolio-by-id'),
    path('artisan-portfolio/legacy/create/', CreateLegacyPortfolioProjectView.as_view(), name='create-legacy-portfolio')

]

