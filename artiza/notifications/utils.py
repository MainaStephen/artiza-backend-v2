from firebase_admin import messaging
from .models import PushToken

def send_push_to_user(user, title, body, data=None):
    tokens = list(PushToken.objects.filter(user=user).values_list("token", flat=True))
    if not tokens:
        return

    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
            data=data or {},
        )
        try:
            messaging.send(message)
            print(f"Notification sent to token: {token}")
        except Exception as e:
            print(f"Failed to send notification to token {token}: {e}")
