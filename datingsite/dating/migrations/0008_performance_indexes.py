from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dating', '0007_alter_post_content'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['created_at']},
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['hide_from_search', 'gender'], name='dating_up_hide_ge_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['-updated_at'], name='dating_up_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='pass',
            index=models.Index(fields=['from_user', 'to_user'], name='dating_pass_from_to_idx'),
        ),
        migrations.AddIndex(
            model_name='pass',
            index=models.Index(fields=['from_user', '-created_at'], name='dating_pass_from_cr_idx'),
        ),
        migrations.AddIndex(
            model_name='like',
            index=models.Index(fields=['from_user', 'to_user'], name='dating_like_from_to_idx'),
        ),
        migrations.AddIndex(
            model_name='like',
            index=models.Index(fields=['to_user', '-created_at'], name='dating_like_to_cr_idx'),
        ),
        migrations.AddIndex(
            model_name='like',
            index=models.Index(fields=['from_user', '-created_at'], name='dating_like_from_cr_idx'),
        ),
        migrations.AddIndex(
            model_name='match',
            index=models.Index(fields=['user1', 'user2'], name='dating_match_users_idx'),
        ),
        migrations.AddIndex(
            model_name='match',
            index=models.Index(fields=['-created_at'], name='dating_match_created_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['match', '-created_at'], name='dating_msg_match_cr_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['match', 'read', 'sender'], name='dating_msg_unread_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['-created_at'], name='dating_post_created_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['user', '-created_at'], name='dating_post_user_cr_idx'),
        ),
    ]
