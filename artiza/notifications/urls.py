from django.urls import path
from .views import SavePushTokenView

urlpatterns = [
    path("save-push-token/", SavePushTokenView.as_view(), name="save_push_token"),
]
