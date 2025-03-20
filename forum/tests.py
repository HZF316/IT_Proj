from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from forum.models import (
    GUser, TopicCircle, Post, Comment, Report, Announcement, UserCircleFollow
)
from forum.forms import (
    GUserCreationForm, NicknameForm, TopicCircleForm, AnnouncementForm
)

User = get_user_model()


# ===========================
# 1. Models Test
class ModelTest(TestCase):

    def setUp(self):
        """
        Create test data.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.circle = TopicCircle.objects.create(
            name='Test Circle',
            description='A circle for testing',
            created_by=self.user
        )
        self.post = Post.objects.create(
            user=self.user,
            circle=self.circle,
            content='Test post content'
        )
        self.announcement = Announcement.objects.create(
            title='Test Announcement',
            content='Announcement content',
            created_by=self.user
        )

    def test_guser_str(self):
        self.assertEqual(str(self.user), 'testuser')

    def test_topiccircle_str(self):
        self.assertEqual(str(self.circle), 'Test Circle')

    def test_post_str(self):
        expected_str = f"Post by {self.user.username} in {self.circle.name}"
        self.assertEqual(str(self.post), expected_str)

    def test_announcement_str(self):
        self.assertEqual(str(self.announcement), 'Test Announcement')


# ===========================
# 2. Views Test
class ViewsTest(TestCase):

    def setUp(self):
        """
        Create normal user, admin user, circle, post, comment, etc., and initialize a test Client.
        """
        self.client = Client()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
  
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass',
            is_admin=True
        )
     
        self.circle = TopicCircle.objects.create(
            name='Extended Test Circle',
            description='A circle for extended testing',
            created_by=self.admin_user
        )
      
        self.post = Post.objects.create(
            user=self.user,
            circle=self.circle,
            content='Extended test post'
        )
       
        self.comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='Extended test comment'
        )

    def test_create_post_view(self):
        """
        checks if the new post is in the database.
        """
        self.client.login(username='testuser', password='testpass')
        url = reverse('create_post', args=[self.circle.id])
        response = self.client.post(url, {'content': 'A new test post content'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(content='A new test post content').exists())

    def test_like_post(self):

        self.client.login(username='testuser', password='testpass')
        url = reverse('like_post', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes, 1)

    def test_dislike_comment(self):

        self.client.login(username='testuser', password='testpass')
        url = reverse('dislike_comment', args=[self.comment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.dislikes, 1)

    def test_unfollow_circle(self):

        # Follow first
        UserCircleFollow.objects.create(user=self.user, circle=self.circle)
        self.client.login(username='testuser', password='testpass')
        url = reverse('unfollow_circle', args=[self.circle.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UserCircleFollow.objects.filter(user=self.user, circle=self.circle).exists())

    def test_admin_post_delete(self):

        self.client.login(username='adminuser', password='adminpass')

        new_post = Post.objects.create(user=self.user, circle=self.circle, content='Admin delete post')
        url = reverse('admin_post_delete', args=[new_post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=new_post.id).exists())

    def test_recommend_post(self):

        self.client.login(username='adminuser', password='adminpass')
        url = reverse('recommend_post', args=[self.post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_recommended)

    def test_admin_dashboard_admin(self):

        self.client.login(username='adminuser', password='adminpass')
        url = reverse('admin_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/admin_dashboard.html')


# ===========================
# 3. Forms Test

class FormsTest(TestCase):
    """
    This class tests form validation logic for Django Forms,
    including valid and invalid inputs.
    """

    def test_guser_creation_form_valid(self):

        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpassit',
            'password2': 'newpassit'
        }
        form = GUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_nickname_form_valid(self):

        form_data = {'nickname': 'nicktest1'}
        form = NicknameForm(data=form_data)
        self.assertTrue(form.is_valid())
