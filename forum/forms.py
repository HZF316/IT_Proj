from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import GUser, TopicCircle, Announcement


class GUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = GUser
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_admin = False  # 确保注册用户不是管理员
        if commit:
            user.save()
        return user

class NicknameForm(forms.Form):
    nickname = forms.CharField(
        max_length=50,
        label="新昵称",
        help_text="昵称长度不超过50字符",
        required=True
    )

    def clean_nickname(self):
        nickname = self.cleaned_data['nickname']
        if len(nickname.strip()) == 0:
            raise forms.ValidationError("昵称不能为空")
        return nickname

class TopicCircleForm(forms.ModelForm):
    class Meta:
        model = TopicCircle
        fields = ['name', 'description', 'is_active']
        labels = {
            'name': '圈子名称',
            'description': '描述',
            'is_active': '是否活跃',
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if TopicCircle.objects.filter(name=name).exclude(id=self.instance.id if self.instance else None).exists():
            raise forms.ValidationError("该圈子名称已存在！")
        return name

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']
        labels = {
            'title': '公告标题',
            'content': '公告内容',
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if not title.strip():
            raise forms.ValidationError("公告标题不能为空")
        return title

    def clean_content(self):
        content = self.cleaned_data['content']
        if not content.strip():
            raise forms.ValidationError("公告内容不能为空")
        return content