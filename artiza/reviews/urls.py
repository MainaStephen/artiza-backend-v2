from django.urls import path
from .views import ProductReviewCreateView, ProductReviewRetrieveView,ProductReviewTestimonialsView

urlpatterns = [
    path('project-review/<int:project_id>/create/', ProductReviewCreateView.as_view(), name='create-review'),
    path('project-review/<int:project_id>/', ProductReviewRetrieveView.as_view(), name='get-review'),
    path('testimonials/', ProductReviewTestimonialsView.as_view(), name='get-testimonials'),
]
