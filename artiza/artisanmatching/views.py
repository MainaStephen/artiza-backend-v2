# from rest_framework import generics, permissions, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
# from django.db.models import Q
# from .models import ArtisanMatch
# from .serializer import ArtisanMatchSerializer
# from projects.models import ProjectRequest
# from users.models import ArtisanProfile, User
# from notifications.utils import send_push_to_user


# # =====================================================
# # 1. ARTISAN: LIST THEIR MATCHED PROJECTS
# # =====================================================
# class ArtisanMatchListView(generics.ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = ArtisanMatchSerializer

#     def get_queryset(self):
#         return ArtisanMatch.objects.filter(
#             artisan=self.request.user
#         ).select_related("project").order_by("-matched_at")


# # =====================================================
# # 2. ARTISAN: MARK MATCH AS VIEWED
# # =====================================================
# class MarkMatchViewedView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request, match_id):
#         match = get_object_or_404(
#             ArtisanMatch,
#             id=match_id,
#             artisan=request.user
#         )
        
#         if match.status == 'pending':
#             match.status = "viewed"
#             match.save()
            
#             # Notify client that artisan viewed the match
#             try:
#                 send_push_to_user(
#                     user=match.project.client,
#                     title="👀 Artisan Viewed Your Project",
#                     body=f"{request.user.full_name} has viewed your project '{match.project.title}'",
#                     data={
#                         "type": "match_viewed",
#                         "project_id": match.project.id,
#                         "artisan_name": request.user.full_name,
#                         "url": "/my-requests"
#                     }
#                 )
#             except Exception as e:
#                 print(f"Failed to send viewed notification: {e}")
            
#             return Response({"message": "Match marked as viewed"})
        
#         return Response({"message": "Match already viewed or responded"}, status=400)


# # =====================================================
# # 3. ARTISAN: ACCEPT / REJECT PROJECT
# # =====================================================
# class RespondToMatchView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request, match_id):
#         action = request.data.get("action")  # "accept" or "reject"
        
#         if action not in ['accept', 'reject']:
#             return Response({
#                 "error": "Invalid action. Use 'accept' or 'reject'."
#             }, status=400)
        
#         match = get_object_or_404(
#             ArtisanMatch,
#             id=match_id,
#             artisan=request.user
#         )
        
#         if action == "accept":
#             match.status = "proposed"
#             message = "You have accepted this project match! The client will be notified."
            
#             # Notify client that artisan accepted
#             try:
#                 send_push_to_user(
#                     user=match.project.client,
#                     title="✅ Artisan Interested in Your Project!",
#                     body=f"{request.user.full_name} is interested in working on '{match.project.title}'. Start chatting now!",
#                     data={
#                         "type": "match_accepted",
#                         "project_id": match.project.id,
#                         "artisan_id": request.user.id,
#                         "artisan_name": request.user.full_name,
#                         "url": f"/my-requests"
#                     }
#                 )
#             except Exception as e:
#                 print(f"Failed to send acceptance notification: {e}")
                
#         else:  # reject
#             match.status = "rejected"
#             message = "You have declined this project match."
        
#         match.save()
        
#         return Response({
#             "message": message,
#             "status": match.status
#         })


# # =====================================================
# # 4. CLIENT: VIEW MATCHED ARTISANS FOR THEIR PROJECT
# # =====================================================
# class ProjectMatchesListView(generics.ListAPIView):
#     """
#     Client endpoint to view all artisans matched to their project
#     """
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = ArtisanMatchSerializer

#     def get_queryset(self):
#         project_id = self.kwargs.get('project_id')
        
#         # Verify the project belongs to the authenticated client
#         project = get_object_or_404(
#             ProjectRequest, 
#             id=project_id, 
#             client=self.request.user
#         )
        
#         # Return all matches for this project with artisan details
#         return ArtisanMatch.objects.filter(
#             project=project
#         ).select_related('artisan').order_by('-matched_at')
    
#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
        
#         # Build enhanced response with artisan details
#         data = []
#         for match in queryset:
#             # Get artisan profile info
#             try:
#                 artisan_profile = ArtisanProfile.objects.get(user=match.artisan)
#                 tier = artisan_profile.tier
#                 completed_projects = getattr(artisan_profile, 'completed_projects', 0)
#                 average_rating = getattr(artisan_profile, 'average_rating', None)
#             except ArtisanProfile.DoesNotExist:
#                 tier = 'bronze'
#                 completed_projects = 0
#                 average_rating = None
            
#             data.append({
#                 'id': match.id,
#                 'artisan_id': match.artisan.id,
#                 'artisan_name': match.artisan.full_name,
#                 'artisan_email': match.artisan.email,
#                 'tier': tier,
#                 'average_rating': average_rating,
#                 'completed_projects': completed_projects,
#                 'status': match.status,
#                 'matched_at': match.matched_at,
#                 'project_id': match.project.id,
#                 'project_title': match.project.title,
#                 'budget': match.project.budget,
#             })
        
#         return Response(data)