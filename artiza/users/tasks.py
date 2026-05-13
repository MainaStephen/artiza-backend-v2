from celery import shared_task
from .emails import send_reset_password_email, send_activation_email

@shared_task
def send_reset_password_email_task(context):
    send_reset_password_email(context)

@shared_task
def send_activation_email_task(context):
    send_activation_email(context)
