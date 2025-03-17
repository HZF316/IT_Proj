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
    # 管理员功能
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/circle/create/', views.circle_create, name='circle_create'),
    path('admin/circle/<int:circle_id>/edit/', views.circle_edit, name='circle_edit'),
    path('admin/circle/<int:circle_id>/delete/', views.circle_delete, name='circle_delete'),
    path('admin/report/<int:report_id>/resolve/', views.report_resolve, name='report_resolve'),
    path('admin/post/<int:post_id>/delete/', views.post_delete, name='post_delete'),
]