from django.urls import path
from .views import ProposalCreateView, ProposalDetailView, ProposalListView, ProposalSelectView,ListArtisanProposals

urlpatterns = [
    # 1️⃣ Create a new proposal (artisan submits a proposal)
    path('create-proposal/', ProposalCreateView.as_view(), name='proposal-create'),

    # 2️⃣ List proposals for a specific project
    path('proposals-list/<int:project_id>/', ProposalListView.as_view(), name='proposal-list'),

    # 3️⃣ Select a proposal (client chooses one proposal) 
    # pass the proposal_id
    path('<int:id>/select/', ProposalSelectView.as_view(), name='proposal-select'),
    
    path('my-proposals/', ListArtisanProposals.as_view(), name='artisan-proposals'),
    
    path('proposal-detail/<int:id>/', ProposalDetailView.as_view(), name='proposal-detail'),
]
