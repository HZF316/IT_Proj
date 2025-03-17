from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import GUser, TopicCircle, Post, Comment, Report

@admin.register(GUser)
class GUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_admin', 'is_staff')
    list_filter = ('is_admin', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('anonymous_nicknames', 'is_admin')}),
    )

@admin.register(TopicCircle)
class TopicCircleAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'is_active')
    list_filter = ('is_active',)
    actions = ['deactivate_circles']

    def deactivate_circles(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_circles.short_description = "Deactivate selected circles"

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'circle', 'created_at', 'is_pinned', 'likes', 'dislikes')
    list_filter = ('circle', 'is_pinned')
    actions = ['pin_posts', 'delete_posts']

    def pin_posts(self, request, queryset):
        queryset.update(is_pinned=True)
    pin_posts.short_description = "Pin selected posts"

    def delete_posts(self, request, queryset):
        queryset.delete()
    delete_posts.short_description = "Delete selected posts"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at', 'is_resolved')
    actions = ['resolve_reports']

    def resolve_reports(self, request, queryset):
        queryset.update(is_resolved=True)
    resolve_reports.short_description = "Mark selected reports as resolved"