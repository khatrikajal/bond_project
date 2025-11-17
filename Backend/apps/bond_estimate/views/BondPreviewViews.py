# apps/bond_estimate/views/BondPreviewViews.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from django.db import transaction

from config.common.response import APIResponse
from apps.bond_estimate.utils.commonutil import get_company_for_user

from apps.bond_estimate.models.PreliminaryBondRequirementsModel import PreliminaryBondRequirements
from apps.bond_estimate.serializers.PreliminaryBondRequirementsSerializer import PreliminaryBondRequirementsSerializer

from apps.bond_estimate.services.bond_preview_service import build_preview_response


class BondPreviewGetView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, company_id):
        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error("Company not found or unauthorized", 404)

        # ✅ Get latest record for this company
        pbr = (
            PreliminaryBondRequirements.objects
            .filter(company=company, del_flag=0)
            .order_by("-created_at")
            .first()
        )

        if not pbr:
            return APIResponse.error("No preliminary bond requirement found", 404)

        return APIResponse.success(
            data=build_preview_response(pbr),
            message="Preview data fetched successfully"
        )
        
class BondPreviewPatchView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def patch(self, request, company_id):
        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error("Company not found or unauthorized", 404)

        # ✅ Get latest record
        pbr = (
            PreliminaryBondRequirements.objects
            .filter(company=company, del_flag=0)
            .order_by("-created_at")
            .first()
        )

        if not pbr:
            return APIResponse.error("No preliminary bond requirement found", 404)

        serializer = PreliminaryBondRequirementsSerializer(
            pbr, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.save(user_id_updated_by=request.user)

        return APIResponse.success(
            data=build_preview_response(pbr),
            message="Record updated successfully"
        )
