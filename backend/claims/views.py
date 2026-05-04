import os
from uuid import uuid4

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Claim
from .services.storage_service import save_uploaded_file
from .services.workflow_service import run_claim_workflow


def serialize_claim(claim):
    workflow_result = claim.workflow_result or None
    if workflow_result and "anomalies" not in workflow_result:
        workflow_result = {
            **workflow_result,
            "anomalies": workflow_result.get("anamolies", []),
        }

    return {
        "id": claim.id,
        "image_url": claim.image_url,
        "status": claim.status,
        "media_type": claim.media_type,
        "workflow_result": workflow_result,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def upload_claim(request):
    if request.method == 'GET':
        claims = (
            Claim.objects.filter(user=request.user)
            .order_by('-id')
        )
        claim_list = [serialize_claim(claim) for claim in claims]
        return Response({"claims": claim_list, "results": claim_list})

    media_type = (request.data.get("media_type") or "image").lower()
    file = request.FILES.get('media') or request.FILES.get('image')

    if not file:
        return Response({"error": "No file uploaded"})

    extension = os.path.splitext(file.name)[1].lower() or ".jpg"
    file_name = f"claims/{request.user.id}/{uuid4().hex}{extension}"

    stored_image = save_uploaded_file(file, file_name)
    image_url = request.build_absolute_uri(stored_image["url"])

    claim = Claim.objects.create(
        user=request.user,
        image_url=image_url,
        status="uploaded",
        media_type=media_type,
    )

    workflow_result = None
    reference_file = request.FILES.get('reference_media') or request.FILES.get('reference_image')

    try:
        reference_path = ""
        if reference_file:
            reference_extension = os.path.splitext(reference_file.name)[1].lower() or ".jpg"
            reference_name = f"claims/{request.user.id}/reference-{uuid4().hex}{reference_extension}"
            stored_reference = save_uploaded_file(reference_file, reference_name)
            reference_path = stored_reference["absolute_path"]

        workflow_result = run_claim_workflow(
            user_id=request.user.id,
            property_id=f"claim-{claim.id}",
            check_out_path=stored_image["absolute_path"],
            check_in_path=reference_path,
            media_type=media_type,
        )
        claim.status = workflow_result.get("status", claim.status)
        claim.workflow_result = workflow_result
        claim.save(update_fields=["status", "workflow_result"])
    except Exception as error:
        workflow_result = {
            "status": f"Workflow error: {error}",
            "anomalies": [],
            "anamolies": [],
            "total_claim_value": 0,
        }
        claim.status = workflow_result["status"]
        claim.workflow_result = workflow_result
        claim.save(update_fields=["status", "workflow_result"])

    return Response({
        "msg": "Uploaded successfully",
        "image_url": image_url,
        "claim_id": claim.id,
        "media_type": media_type,
        "workflow_result": {
            **workflow_result,
            "anomalies": workflow_result.get("anomalies", workflow_result.get("anamolies", [])),
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def claim_detail(request, claim_id):
    try:
        claim = Claim.objects.get(id=claim_id, user=request.user)
    except Claim.DoesNotExist:
        return Response({"detail": "Claim not found"}, status=404)

    return Response(serialize_claim(claim))


def home(request):
    return HttpResponse("""Claimuard AI""")
