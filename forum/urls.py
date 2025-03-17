from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
#   path('login/', views.custom_login, name='login'),
    path('circle/<int:circle_id>/', views.circle_detail, name='circle_detail'),
    path('circle/<int:circle_id>/post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/dislike/', views.dislike_post, name='dislike_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/report/', views.report_post, name='report_post'),
    path('all-circles/', views.all_circles, name='all_circles'),
    path('profile/', views.profile, name='profile'),
]