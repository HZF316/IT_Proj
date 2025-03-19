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
        user.is_admin = False  # admin user can not be registered
        if commit:
            user.save()
        return user

class NicknameForm(forms.Form):
    nickname = forms.CharField(
        max_length=50,
        label="New Nickname",
        help_text="CAN'T LONGER THAN 50 CHARACTERS",
        required=True
    )

    def clean_nickname(self):
        nickname = self.cleaned_data['nickname']
        if len(nickname.strip()) == 0:
            raise forms.ValidationError("CAN'T BE EMPTY")
        return nickname

class TopicCircleForm(forms.ModelForm):
    class Meta:
        model = TopicCircle
        fields = ['name', 'description', 'is_active']
        labels = {
            'name': 'Circle Name',
            'description': 'Description',
            'is_active': 'Whether the circle is active',
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if TopicCircle.objects.filter(name=name).exclude(id=self.instance.id if self.instance else None).exists():
            raise forms.ValidationError("Circle with this name already exists")
        return name

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']
        labels = {
            'title': 'Announcement Title',
            'content': 'Announcement Content',
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if not title.strip():
            raise forms.ValidationError("ANNOUNCEMENT TITLE EMPTY")
        return title

    def clean_content(self):
        content = self.cleaned_data['content']
        if not content.strip():
            raise forms.ValidationError("ANNOUNCEMENT CONTENT EMPTY")
        return content