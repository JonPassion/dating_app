from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dating', '0008_performance_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='media_file',
            field=models.FileField(blank=True, null=True, upload_to='chat_media/'),
        ),
        migrations.AddField(
            model_name='message',
            name='media_type',
            field=models.CharField(
                blank=True,
                choices=[('image', 'Image'), ('video', 'Video')],
                default='',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='message',
            name='content',
            field=models.TextField(blank=True, default=''),
        ),
    ]
