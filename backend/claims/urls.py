from django.urls import path
from .views import claim_detail, upload_claim

urlpatterns=[
    path('uploads/', upload_claim),
    path('uploads/<int:claim_id>/', claim_detail),
]
