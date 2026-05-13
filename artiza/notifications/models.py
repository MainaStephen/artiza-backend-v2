# from django.db import models
# from django.contrib.auth.models import User

# class PushToken(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     token = models.TextField(unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)


# notifications/models.py
from django.db import models
from django.conf import settings

class PushToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} – {self.token[:10]}…"
