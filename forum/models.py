from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# 自定义用户模型 GUser
class GUser(AbstractUser):
    email = models.EmailField(unique=True)  # 邮箱作为唯一标识
    anonymous_nicknames = models.JSONField(default=list, blank=True)  # 存储多个匿名昵称
    is_admin = models.BooleanField(default=False)  # 区分普通用户和管理员

    def __str__(self):
        return self.username

# 话题圈模型
class TopicCircle(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(GUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_admin': True})  # 仅管理员创建
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# 帖子模型
class Post(models.Model):
    user = models.ForeignKey(GUser, on_delete=models.CASCADE)
    circle = models.ForeignKey(TopicCircle, on_delete=models.CASCADE)
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    nickname = models.CharField(max_length=50, blank=True, null=True)  # 匿名时使用
    location = models.CharField(max_length=100, blank=True, null=True)  # 可选实时位置
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"Post by {self.user.username if not self.is_anonymous else self.nickname} in {self.circle.name}"

# 评论模型
class Comment(models.Model):
    user = models.ForeignKey(GUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post}"

# 举报模型
class Report(models.Model):
    user = models.ForeignKey(GUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report on {self.post} by {self.user.username}"