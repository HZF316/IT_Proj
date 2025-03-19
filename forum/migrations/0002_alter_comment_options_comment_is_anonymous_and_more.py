# Generated by Django 5.1.1 on 2025-03-17 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='comment',
            name='is_anonymous',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='comment',
            name='nickname',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
