from django.urls import path
from .views import (
    # CombinedProjectMessagesView,
    ProjectUpdatesPostView,
    ProjectMessageView,
    CombinedMarkReadView,
    FlaggedMessagesView,
    ReviewFlaggedMessageView,
    ProjectUpdatesPostView
)

urlpatterns = [
    path("messages/<int:project_id>/", ProjectMessageView.as_view()),
    path("post-updates/<int:project_id>/", ProjectUpdatesPostView.as_view()),
    path("mark-messages-as-read/<int:project_id>/mark-all-read/", CombinedMarkReadView.as_view()),

    # Admin moderation
    path("admin/flagged-messages/", FlaggedMessagesView.as_view(), name="flagged-messages"),
    path("admin/flagged-messages/<int:message_id>/review/", ReviewFlaggedMessageView.as_view(), name="review-flagged-message"),
    # path("combined-messages/<int:project_id>/", CombinedProjectMessagesView.as_view()),
]
