import re
from .models import NegotiationMessage

# -------------------------------------------------
# DETECTION FUNCTIONS
# -------------------------------------------------

def detect_phone_number(text):
    """
    Detects any phone number in the text.
    Matches formats like:
    - +254712345678
    - 0712345678
    - 07 123 45678
    - 0712-345-678
    - +254 712 345 678
    - 0712.345.678
    """
    if not text:
        return False

    phone_pattern = r"(\+?\d[\d .-]{7,}\d)"
    return bool(re.search(phone_pattern, text))


def detect_email(text):
    """Detects any email addresses in the text."""
    if not text:
        return False
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return bool(re.search(email_pattern, text))


def detect_url(text):
    """Detects any URLs in the text."""
    if not text:
        return False
    url_pattern = r"(https?://\S+|www\.\S+)"
    return bool(re.search(url_pattern, text))


def detect_off_platform_content(text):
    """
    Returns True if the text contains phone numbers, emails, or URLs.
    """
    return detect_phone_number(text) or detect_email(text) or detect_url(text)


def detect_intent_phrases(text):
    """
    Returns True if the text contains intent to move off the platform.
    """
    if not text:
        return False

    intent_phrases = [
        "contact me",
        "call me",
        "text me",
        "whatsapp me",
        "reach me",
        "off the app",
        "outside the app",
        "message me directly",
        "hit me up",
        "dm me",
        "send your phone number",
    ]

    text_lower = text.lower()
    return any(phrase in text_lower for phrase in intent_phrases)


# -------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------

def should_block_negotiation_message(proposal_id, user, message_text):
    """
    Determines whether a negotiation message should be flagged or blocked.

    Returns:
        flagged (bool): Whether the message should be flagged.
        blocked (bool): Whether the message should be blocked from sending.
    """
    contains_phone = detect_phone_number(message_text)
    contains_email = detect_email(message_text)
    contains_url = detect_url(message_text)
    contains_intent = detect_intent_phrases(message_text)

    # Count previous flagged messages by this user in this proposal
    previous_flags = NegotiationMessage.objects.filter(
        negotiation__proposal_id=proposal_id,
        sender=user,
        flagged=True
    ).count()

    # -------------------------------------------------
    # STRICT BLOCKING RULES
    # -------------------------------------------------
    # Block if any phone number, email, or URL is detected
    if contains_phone or contains_email or contains_url:
        return True, True  # flagged + blocked

    # Block if intent phrases are repeated
    if contains_intent and previous_flags >= 1:
        return True, True  # flagged + blocked

    # First offense of intent phrases → flag only
    if contains_intent:
        return True, False

    # Safe message → no flag, no block
    return False, False
