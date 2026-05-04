# Generated for ClaimGuard frontend integration.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('claims', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='claim',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='claim',
            name='media_type',
            field=models.CharField(default='image', max_length=20),
        ),
        migrations.AddField(
            model_name='claim',
            name='workflow_result',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
