from django.urls import path
from .views import (
    ArtisanProjectDetailView,
    ClientRequestListCreateView,
    ClientRequestDetailView,
    ListClientProjectsView,
    ListArtisanAcceptedProjects,
    ClientProjectsWithUpdatesView,
    ArtisanDashboardView,
    ClientDashboardView,
    AdminDashboardView,
    ProjectsManagementView,
    ReadyMadeProductsListCreateView,
    ReadyMadeProductDetailView,
    ClientReadyProductsListView,
    ArtisanMatchedProjectsView,
    MarkMatchedProjectViewedView,
    RespondToMatchedProjectView,
    ProjectMatchedArtisansView,
)


urlpatterns = [
    # Client routes
    path("create-project/", ClientRequestListCreateView.as_view(), name="client-requests"),
    # one client project
    path("client-project/<int:pk>/", ClientRequestDetailView.as_view(), name="client-request-detail"),
    # all client projects
    path("client-projects/", ListClientProjectsView.as_view(), name="client-request-list"),
    path("client-project-updates/", ClientProjectsWithUpdatesView.as_view(), name="client-request-list"),
    path("client-dashboard/", ClientDashboardView.as_view(), name="client-dashboard"),

    # Artisan apis

    path("accepted-projects/", ListArtisanAcceptedProjects.as_view(), name="accepted-projects"),
    path("artisan-dashboard/", ArtisanDashboardView.as_view(), name="artisan-dashboard"),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard-stats'),
    path('admin/project-management/', ProjectsManagementView.as_view(), name='admin-dashboard-stats'),


# ready made products
    path('ready-made-products/', ReadyMadeProductsListCreateView.as_view(), name='ready-made-products'),
    # update/delete one ready made product
    path('ready-made-products/<int:pk>/', ReadyMadeProductDetailView.as_view(), name='ready-made-product-detail'),
    path('client-list-ready-made-products/', ClientReadyProductsListView.as_view(), name='client-ready-made-products'),
    
    
    
    # =====================================================
    # ARTISAN MATCHED PROJECTS
    # =====================================================

    path(
        "artisan/matched-projects/",
        ArtisanMatchedProjectsView.as_view(),
        name="artisan-matched-projects"
    ),

    path(
        "artisan/matched-projects/<int:match_id>/view/",
        MarkMatchedProjectViewedView.as_view(),
        name="matched-project-viewed"
    ),

    path(
        "artisan/matched-projects/<int:match_id>/respond/",
        RespondToMatchedProjectView.as_view(),
        name="matched-project-respond"
    ),

    path("artisan-project/<int:pk>/", ArtisanProjectDetailView.as_view(), name="artisan-project-detail"),
    # =====================================================
    # CLIENT PROJECT MATCHES
    # =====================================================

    path(
        "client/projects/<int:project_id>/matches/",
        ProjectMatchedArtisansView.as_view(),
        name="project-matched-artisans"
    ),
]
