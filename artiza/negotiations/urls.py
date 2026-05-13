# negotiations/urls.py
from django.urls import path
from .views import (
    NegotiationMessageListCreateView, 
    NegotiationDetailView,
    SubmitFinalAgreementView,
    AcceptFinalAgreementView,
    UnreadNegotiationsCountView,
    
   ProposalUnreadCountView,
    MarkProposalMessagesAsReadView,  # Add this import
    NegotiationListView
)

urlpatterns = [
    path('inbox/', NegotiationListView.as_view()),
    path(
        'proposal/<int:proposal_id>/messages/',
        NegotiationMessageListCreateView.as_view(),
        name='negotiation-messages'
    ),
    path(
        'proposal/<int:proposal_id>/',
        NegotiationDetailView.as_view(),
        name='negotiation-detail'
    ),
    

    path(
        'proposal/<int:proposal_id>/unread-count/',
        ProposalUnreadCountView.as_view(),
        name='proposal-unread-count'
    ),
    path(
        'proposal/<int:proposal_id>/mark-as-read/',
        MarkProposalMessagesAsReadView.as_view(),
        name='mark-proposal-messages-read'
    ),

    path(
        'submit-final-agreement/<int:pk>/',
        SubmitFinalAgreementView.as_view(),
        name='submit-final-agreement'
    ),
    path(
        'accept-final-agreement/<int:pk>/',
        AcceptFinalAgreementView.as_view(),
        name='accept-final-agreement'
    ),
    
    path(
        'unread-count/',
        UnreadNegotiationsCountView.as_view(),
        name='unread-negotiations-count'
    ),
    

]