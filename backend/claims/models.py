from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Claim(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_url = models.URLField()
    status = models.CharField(max_length=50, default='pending')
    media_type = models.CharField(max_length=20, default='image')
    workflow_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
