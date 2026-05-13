# import threading
# from django.conf import settings
# from sib_api_v3_sdk import ApiClient, Configuration
# from sib_api_v3_sdk.api.transactional_emails_api import TransactionalEmailsApi


# # ------------------------------------------------------------------
# # Internal: Send email via Brevo
# # ------------------------------------------------------------------
# def _send_brevo_email(payload: dict):
#     try:
#         config = Configuration()
#         config.api_key['api-key'] = settings.BREVO_API_KEY

#         api_client = ApiClient(config)
#         email_api = TransactionalEmailsApi(api_client)

#         email_api.send_transac_email(payload)

#     except Exception as e:
#         # In production, replace print with logging
#         print("Brevo email error:", e)


# def send_email_async(payload: dict):
#     """
#     Send email in a background thread to avoid blocking requests.
#     """
#     thread = threading.Thread(
#         target=_send_brevo_email,
#         args=(payload,),
#         daemon=True
#     )
#     thread.start()


# # ------------------------------------------------------------------
# # Password Reset Email
# # ------------------------------------------------------------------
# def send_reset_password_email(context: dict):
#     """
#     context expects:
#       - reset_url (str)
#       - user (User) OR email (str)
#     """
#     user = context.get("user")
#     email = user.email if user else context.get("email")
#     name = getattr(user, "full_name", "there")
#     reset_url = context.get("reset_url")

#     payload = {
#         "sender": {
#             "email": settings.DEFAULT_FROM_EMAIL,
#             "name": "ARTIZA"
#         },
#         "to": [{"email": email}],
#         "subject": "🔑 Reset Your ARTIZA Password",
#         "htmlContent": f"""
#         <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:40px 0;">
#           <tr>
#             <td align="center">
#               <table width="600" cellpadding="0" cellspacing="0"
#                      style="background:#ffffff;border-radius:12px;padding:40px;font-family:Arial;">
                
#                 <tr>
#                   <td align="center" style="font-size:24px;font-weight:bold;color:#111827;">
#                     Reset Your Password
#                   </td>
#                 </tr>

#                 <tr>
#                   <td style="font-size:16px;color:#374151;padding:20px 0;">
#                     Hello <strong>{name}</strong>,<br><br>
#                     Click the button below to reset your password.
#                   </td>
#                 </tr>

#                 <tr>
#                   <td align="center" style="padding:20px 0;">
#                     <a href="{reset_url}"
#                        style="background:#4f46e5;color:#ffffff;padding:14px 28px;
#                               text-decoration:none;border-radius:8px;font-weight:bold;">
#                       Reset Password
#                     </a>
#                   </td>
#                 </tr>

#                 <tr>
#                   <td style="font-size:14px;color:#6b7280;">
#                     Or copy this link:<br>
#                     {reset_url}
#                   </td>
#                 </tr>

#               </table>
#             </td>
#           </tr>
#         </table>
#         """,
#         "textContent": f"Hello {name}, reset your password here: {reset_url}"
#     }

#     send_email_async(payload)


# # ------------------------------------------------------------------
# # Account Activation Email
# # ------------------------------------------------------------------
# def send_activation_email(context: dict):
#     """
#     context expects:
#       - activation_url (str)
#       - user (User) OR email (str)
#     """
#     user = context.get("user")
#     email = user.email if user else context.get("email")
#     name = getattr(user, "full_name", "there")
#     activation_url = context.get("activation_url")

#     payload = {
#         "sender": {
#             "email": settings.DEFAULT_FROM_EMAIL,
#             "name": "ARTIZA"
#         },
#         "to": [{"email": email}],
#         "subject": "✅ Activate Your ARTIZA Account",
#         "htmlContent": f"""
#         <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:40px 0;">
#           <tr>
#             <td align="center">
#               <table width="600" cellpadding="0" cellspacing="0"
#                      style="background:#ffffff;border-radius:12px;padding:40px;font-family:Arial;">
                
#                 <tr>
#                   <td align="center" style="font-size:24px;font-weight:bold;color:#111827;">
#                     Activate Your Account
#                   </td>
#                 </tr>

#                 <tr>
#                   <td style="font-size:16px;color:#374151;padding:20px 0;">
#                     Hello <strong>{name}</strong>,<br><br>
#                     Click the button below to activate your ARTIZA account.
#                   </td>
#                 </tr>

#                 <tr>
#                   <td align="center" style="padding:20px 0;">
#                     <a href="{activation_url}"
#                        style="background:#10b981;color:#ffffff;padding:14px 28px;
#                               text-decoration:none;border-radius:8px;font-weight:bold;">
#                       Activate Account
#                     </a>
#                   </td>
#                 </tr>

#                 <tr>
#                   <td style="font-size:14px;color:#6b7280;">
#                     Or copy this link:<br>
#                     {activation_url}
#                   </td>
#                 </tr>

#               </table>
#             </td>
#           </tr>
#         </table>
#         """,
#         "textContent": f"Hello {name}, activate your account here: {activation_url}"
#     }

#     send_email_async(payload)




import threading
from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration
from sib_api_v3_sdk.api.transactional_emails_api import TransactionalEmailsApi


# ------------------------------------------------------------------
# Internal: Send email via Brevo
# ------------------------------------------------------------------
def _send_brevo_email(payload: dict):
    try:
        config = Configuration()
        config.api_key['api-key'] = settings.BREVO_API_KEY

        api_client = ApiClient(config)
        email_api = TransactionalEmailsApi(api_client)

        email_api.send_transac_email(payload)

    except Exception as e:
        # In production, replace print with logging
        print("Brevo email error:", e)


def send_email_async(payload: dict):
    """
    Send email in a background thread to avoid blocking requests.
    """
    thread = threading.Thread(
        target=_send_brevo_email,
        args=(payload,),
        daemon=True
    )
    thread.start()


# ------------------------------------------------------------------
# Base HTML template for emails
# ------------------------------------------------------------------
def _build_email_html(content_title: str, message: str, button_text: str, button_url: str):
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:40px 0;">
      <tr>
        <td align="center">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="background:#ffffff;border-radius:12px;padding:40px;font-family:Arial, sans-serif;">
            
            <tr>
              <td align="center" style="padding-bottom:30px;">
                <img src="https://artiza.co.ke/static/media/logo7.f986c36849e6bb3c42e8.png" 
                     alt="ARTIZA" width="150" style="display:block;">
              </td>
            </tr>

            <tr>
              <td align="center" style="font-size:24px;font-weight:bold;color:#111827;padding-bottom:20px;">
                {content_title}
              </td>
            </tr>

            <tr>
              <td style="font-size:16px;color:#374151;padding-bottom:30px;">
                {message}
              </td>
            </tr>

            <tr>
              <td align="center" style="padding-bottom:20px;">
                <a href="{button_url}"
                   style="background:#673200;color:#ffffff;padding:14px 28px;
                          text-decoration:none;border-radius:8px;font-weight:bold;">
                  {button_text}
                </a>
              </td>
            </tr>

            <tr>
              <td style="font-size:14px;color:#6b7280;">
                Or copy this link:<br>
                {button_url}
              </td>
            </tr>

            <tr>
              <td style="font-size:12px;color:#9ca3af;padding-top:30px;text-align:center;">
                If you did not request this, please ignore this email.
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
    """


# ------------------------------------------------------------------
# Password Reset Email
# ------------------------------------------------------------------
def send_reset_password_email(context: dict):
    """
    context expects:
      - reset_url (str)
      - user (User) OR email (str)
    """
    user = context.get("user")
    email = user.email if user else context.get("email")
    name = getattr(user, "full_name", "there")
    reset_url = context.get("reset_url")

    html_content = _build_email_html(
        content_title="Reset Your Password",
        message=f"Hello <strong>{name}</strong>,<br><br>Click the button below to reset your password.",
        button_text="Reset Password",
        button_url=reset_url
    )

    payload = {
        "sender": {
            "email": settings.DEFAULT_FROM_EMAIL,
            "name": "ARTIZA"
        },
        "to": [{"email": email}],
        "subject": "🔑 Reset Your ARTIZA Password",
        "htmlContent": html_content,
        "textContent": f"Hello {name}, reset your password here: {reset_url}"
    }

    send_email_async(payload)


# ------------------------------------------------------------------
# Account Activation Email
# ------------------------------------------------------------------
def send_activation_email(context: dict):
    """
    context expects:
      - activation_url (str)
      - user (User) OR email (str)
    """
    user = context.get("user")
    email = user.email if user else context.get("email")
    name = getattr(user, "full_name", "there")
    activation_url = context.get("activation_url")

    html_content = _build_email_html(
        content_title="Activate Your Account",
        message=f"Hello <strong>{name}</strong>,<br><br>Click the button below to activate your ARTIZA account.",
        button_text="Activate Account",
        button_url=activation_url
    )

    payload = {
        "sender": {
            "email": settings.DEFAULT_FROM_EMAIL,
            "name": "ARTIZA"
        },
        "to": [{"email": email}],
        "subject": "✅ Activate Your ARTIZA Account",
        "htmlContent": html_content,
        "textContent": f"Hello {name}, activate your account here: {activation_url}"
    }

    send_email_async(payload)
