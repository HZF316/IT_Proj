# Generated by Django 5.1.1 on 2025-03-18 00:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0005_comment_dislikes_comment_likes'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_recommended',
            field=models.BooleanField(default=False),
        ),
    ]
