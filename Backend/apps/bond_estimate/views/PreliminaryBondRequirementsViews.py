# apps/bond_estimate/views/PreliminaryBondRequirementsViews.py

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework import status

from config.common.response import APIResponse

from apps.bond_estimate.utils.commonutil import (
    get_company_for_user,
    paginate_queryset,
    update_step_status,
)

from apps.bond_estimate.models.PreliminaryBondRequirementsModel import PreliminaryBondRequirements
from apps.bond_estimate.serializers.PreliminaryBondRequirementsSerializer import PreliminaryBondRequirementsSerializer

from apps.bond_estimate.services.bond_estimation_service import (
    create_or_get_application,
    update_step,
)


STEP_ID = "4.1"
MAIN_STEP = "4"


class PreliminaryBondRequirementsListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request, company_id):
        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error(
                message="Company not found or access denied",
                status_code=404
            )

        qs = (
            PreliminaryBondRequirements.objects
            .select_related("company")
            .filter(company=company, del_flag=0)
            .order_by("-created_at")
        )

        items, meta = paginate_queryset(qs, request)
        serializer = PreliminaryBondRequirementsSerializer(items, many=True)

        return APIResponse.success(
            data={
                "items": serializer.data,
                "meta": meta
            },
            message="Preliminary bond requirements fetched successfully"
        )

    def post(self, request, company_id):
        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error(
                message="Company not found or access denied",
                status_code=404
            )

        data = request.data.copy()
        data["company"] = str(company.company_id)

        serializer = PreliminaryBondRequirementsSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            instance = serializer.save(user_id_updated_by=request.user)

            # Step tracking
            application = create_or_get_application(request.user, company)

            update_step(
                application,
                step_id=STEP_ID,
                record_ids=[str(instance.id)],
                completed=True,
            )

            # Update main step 4
            update_step_status(application, MAIN_STEP)

        return APIResponse.success(
            data=PreliminaryBondRequirementsSerializer(instance).data,
            message="Preliminary bond requirement created successfully",
            status_code=201
        )


class PreliminaryBondRequirementsDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    # -------------------------------
    # Fetch record with company check
    # -------------------------------
    def get_object(self, company_id, pbr_id, user):
        company = get_company_for_user(company_id, user)
        if not company:
            return None, APIResponse.error(
                message="Company not found or access denied",
                status_code=404
            )

        try:
            obj = (
                PreliminaryBondRequirements.objects
                .select_related("company")
                .get(id=pbr_id, company=company, del_flag=0)
            )
            return obj, None

        except PreliminaryBondRequirements.DoesNotExist:
            return None, APIResponse.error(
                message="Record not found",
                status_code=404
            )

    # -------------------------------
    # GET
    # -------------------------------
    def get(self, request, company_id, pbr_id):
        obj, error = self.get_object(company_id, pbr_id, request.user)
        if error:
            return error

        return APIResponse.success(
            data=PreliminaryBondRequirementsSerializer(obj).data,
            message="Record fetched successfully"
        )

    # -------------------------------
    # PUT (Full update)
    # -------------------------------
    def put(self, request, company_id, pbr_id):
        obj, error = self.get_object(company_id, pbr_id, request.user)
        if error:
            return error

        data = request.data.copy()
        data["company"] = str(obj.company.company_id)

        serializer = PreliminaryBondRequirementsSerializer(
            obj, data=data, partial=False
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            updated = serializer.save(user_id_updated_by=request.user)

            # Step 4.1 stays completed
            application = create_or_get_application(request.user, obj.company)
            update_step(
                application,
                step_id=STEP_ID,
                record_ids=[str(obj.id)],
                completed=True,
            )

            update_step_status(application, MAIN_STEP)

        return APIResponse.success(
            data=PreliminaryBondRequirementsSerializer(updated).data,
            message="Record updated successfully"
        )

    # -------------------------------
    # PATCH (Partial update)
    # -------------------------------
    def patch(self, request, company_id, pbr_id):
        obj, error = self.get_object(company_id, pbr_id, request.user)
        if error:
            return error

        data = request.data.copy()
        data["company"] = str(obj.company.company_id)

        serializer = PreliminaryBondRequirementsSerializer(
            obj, data=data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            updated = serializer.save(user_id_updated_by=request.user)

            # Step tracking same as PUT
            application = create_or_get_application(request.user, obj.company)
            update_step(
                application,
                step_id=STEP_ID,
                record_ids=[str(obj.id)],
                completed=True,
            )

            update_step_status(application, MAIN_STEP)

        return APIResponse.success(
            data=PreliminaryBondRequirementsSerializer(updated).data,
            message="Record updated successfully (partial)"
        )

    # -------------------------------
    # DELETE (Soft delete)
    # -------------------------------
    def delete(self, request, company_id, pbr_id):
        obj, error = self.get_object(company_id, pbr_id, request.user)
        if error:
            return error

        with transaction.atomic():
            obj.del_flag = 1
            obj.user_id_updated_by = request.user
            obj.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

            company = obj.company
            application = create_or_get_application(request.user, company)

            remaining = PreliminaryBondRequirements.objects.filter(
                company=company, del_flag=0
            ).exists()

            update_step(
                application,
                step_id=STEP_ID,
                record_ids=[],
                completed=remaining,
            )

            update_step_status(application, MAIN_STEP)

        return APIResponse.success(
            message="Record deleted successfully"
        )
