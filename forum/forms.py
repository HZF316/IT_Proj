from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import GUser

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