from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model


class GUser(AbstractUser):
    email = models.EmailField(unique=True)
    anonymous_nicknames = models.JSONField(default=list, blank=True)  # store many nicknames
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class TopicCircle(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(GUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_admin': True})  # only admin user can do this
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    user = models.ForeignKey(GUser, on_delete=models.CASCADE)
    circle = models.ForeignKey(TopicCircle, on_delete=models.CASCADE)
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    nickname = models.CharField(max_length=50, blank=True, null=True)  # used when want to be anonymous
    location = models.CharField(max_length=100, blank=True, null=True)  # real time location
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Post by {self.user.username if not self.is_anonymous else self.nickname} in {self.circle.name}"

class Comment(models.Model):
    user = models.ForeignKey(GUser, on_delete=models.CASCADE)
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)
    nickname = models.CharField(max_length=50, blank=True, null=True)
    likes = models.IntegerField(default=0)  # new likes
    dislikes = models.IntegerField(default=0)  # new comments
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        if self.is_anonymous:
            return f"{self.nickname or 'Anonymous'}: {self.content[:20]}"
        return f"{self.user.username}: {self.content[:20]}"

    class Meta:
        ordering = ['-created_at']

class Report(models.Model):
    user = models.ForeignKey(GUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report on {self.post} by {self.user.username}"

class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name="Announcement Title")
    content = models.TextField(verbose_name="Announcement Content")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    created_by = models.ForeignKey(GUser, on_delete=models.SET_NULL, null=True, verbose_name="Created By")
    is_pinned = models.BooleanField(default=False, verbose_name="Whether pin")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-is_pinned', '-created_at']

class UserCircleFollow(models.Model):
    user = models.ForeignKey(GUser, on_delete=models.CASCADE, verbose_name="GUser")
    circle = models.ForeignKey('TopicCircle', on_delete=models.CASCADE, verbose_name="Circle")
    followed_at = models.DateTimeField(auto_now_add=True, verbose_name="Followed At")

    class Meta:
        unique_together = ('user', 'circle')
        verbose_name = "User Circle Follow"
        verbose_name_plural = "User Circle Follow"

    def __str__(self):
        return f"{self.user.username} follow {self.circle.name}"