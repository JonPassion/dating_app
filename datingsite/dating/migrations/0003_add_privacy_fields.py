from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dating', '0002_alter_userprofile_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='anonymous_id',
            field=models.CharField(blank=True, max_length=10, unique=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='anonymous_mode',
            field=models.BooleanField(default=True, help_text='Hide username and use anonymous ID'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='hide_from_search',
            field=models.BooleanField(default=False, help_text="Don't appear in browse results"),
        ),
    ]
