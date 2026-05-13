# import random

# from users.models import ArtisanProfile
# from .models import ArtisanMatch



# def match_artisans_to_project(project):
#     print("🔥 MATCH FUNCTION STARTED")
#     print("Project:", project.id, project.budget)
    
    
    
# # =========================================
# # Tier Weights
# # =========================================
# TIER_WEIGHTS = {
#     "bronze": 1,
#     "silver": 2,
#     "gold": 3,
#     "premium": 4,
# }


# # =========================================
# # Match Function
# # =========================================
# def match_artisans_to_project(project):

#     budget = project.budget

#     # =========================================
#     # Budget → Allowed Tiers
#     # =========================================
#     if budget <= 5000:
#         allowed_tiers = ["bronze"]

#     elif budget <= 20000:
#         allowed_tiers = ["bronze", "silver"]

#     elif budget <= 50000:
#         allowed_tiers = ["silver", "gold"]

#     else:
#         allowed_tiers = ["gold", "premium"]

#     # =========================================
#     # Get Eligible Artisans
#     # =========================================
#     artisans = ArtisanProfile.objects.filter(
#         tier__in=allowed_tiers,
#         user__is_active=True,
#         user__role="artisan"
#     ).select_related("user")

#     # =========================================
#     # Score Artisans
#     # =========================================
#     ranked_artisans = sorted(
#         artisans,
#         key=lambda artisan: (
#             artisan.average_rating * 5
#             + artisan.completed_projects * 2
#             + TIER_WEIGHTS.get(artisan.tier, 0)
#         ),
#         reverse=True
#     )

#     # =========================================
#     # Candidate Pool
#     # =========================================
#     candidate_pool = ranked_artisans[:15]

#     # =========================================
#     # Randomly Select 5
#     # =========================================
#     selected_artisans = random.sample(
#         candidate_pool,
#         min(5, len(candidate_pool))
#     )

#     # =========================================
#     # Save Matches
#     # =========================================
#     for artisan in selected_artisans:

#         ArtisanMatch.objects.get_or_create(
#             project=project,
#             artisan=artisan.user
#         )

#     return selected_artisans



import random
from notifications.utils import send_push_to_user
from users.models import ArtisanProfile
from .models import ArtisanMatch


# =========================================
# Tier Weights
# =========================================
TIER_WEIGHTS = {
    "bronze": 1,
    "silver": 2,
    "gold": 3,
    "premium": 4,
}


# =========================================
# Match Function
# =========================================
def match_artisans_to_project(project):
    print("🔥 MATCH FUNCTION STARTED")
    print("Project:", project.id, project.budget)

    budget = project.budget

    # =========================================
    # Budget → Allowed Tiers
    # =========================================
    if budget <= 5000:
        allowed_tiers = ["bronze"]
    elif budget <= 20000:
        allowed_tiers = ["bronze", "silver"]
    elif budget <= 50000:
        allowed_tiers = ["silver", "gold"]
    else:
        allowed_tiers = ["gold", "premium"]

    print(f"Allowed tiers: {allowed_tiers}")

    # =========================================
    # Get Eligible Artisans
    # =========================================
    artisans = ArtisanProfile.objects.filter(
        tier__in=allowed_tiers,
        user__is_active=True,
        user__role="artisan"
    ).select_related("user")

    print(f"Total eligible artisans: {artisans.count()}")

    # =========================================
    # Score Artisans
    # =========================================
    ranked_artisans = sorted(
        artisans,
        key=lambda artisan: (
            (artisan.average_rating or 0) * 5
            + (artisan.completed_projects or 0) * 2
            + TIER_WEIGHTS.get(artisan.tier, 0)
        ),
        reverse=True
    )

    # =========================================
    # Candidate Pool
    # =========================================
    candidate_pool = ranked_artisans[:15]
    print(f"Candidate pool size: {len(candidate_pool)}")

    # =========================================
    # Randomly Select 5
    # =========================================
    selected_artisans = random.sample(
        candidate_pool,
        min(5, len(candidate_pool))
    )
    print(f"Selected artisans: {len(selected_artisans)}")

    # =========================================
    # Save Matches and Send Notifications
    # =========================================
    for artisan_profile in selected_artisans:
        artisan = artisan_profile.user
        
        # Create or get the match
        match, created = ArtisanMatch.objects.get_or_create(
            project=project,
            artisan=artisan
        )
        
        if created:
            print(f"Created match for artisan: {artisan.full_name}")
            
            # Format budget for display
            formatted_budget = f"KSh {float(project.budget):,.0f}"
            
            # Send push notification to artisan
            try:
                send_push_to_user(
                    user=artisan,
                    title="🎯 New Project Match!",
                    body=f"You've been matched with a new project: {project.title} (Budget: {formatted_budget})",
                    data={
                        "type": "project_match",
                        "match_id": match.id,
                        "project_id": project.id,
                        "project_title": project.title,
                        "budget": str(project.budget),
                        "url": "/artisan-matches"
                    }
                )
                print(f"Notification sent to {artisan.full_name}")
            except Exception as e:
                print(f"Failed to send notification to {artisan.full_name}: {e}")
        else:
            print(f"Match already existed for artisan: {artisan.full_name}")

    # =========================================
    # Also create a notification for the client
    # =========================================
    try:
        from notifications.models import Notification
        
        Notification.objects.create(
            user=project.client,
            title="Artisans Found! 🎉",
            message=f"We've found {len(selected_artisans)} skilled artisans who match your project '{project.title}'. Check your matches now!",
            notification_type="match",
            related_object_id=project.id,
            related_object_type="project"
        )
        print(f"Client notification created for {project.client.email}")
    except Exception as e:
        print(f"Failed to create client notification: {e}")

    return selected_artisans