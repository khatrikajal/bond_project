from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.db import transaction

from config.common.response import APIResponse
from apps.bond_estimate.utils.commonutil import (
    get_company_for_user,
    paginate_queryset,
    get_object_or_error,
    update_step_status
)

from apps.bond_estimate.models.CollateralAssetVerificationModel import (
    CollateralAssetVerification
)
from apps.bond_estimate.serializers.CollateralAssetVerificationSerializer import (
    CollateralAssetVerificationSerializer,
    CollateralAssetVerificationDetailSerializer,
)

from apps.bond_estimate.services.bond_estimation_service import (
    create_or_get_application,
    update_step,
)


SUB_STEP = "4.2"
MAIN_STEP = "4"


# =====================================================================
# LIST + CREATE
# =====================================================================
class CollateralAssetVerificationListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # -----------------------------------------------------------------
    def get(self, request, company_id):

        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error("Company not found or access denied.", status_code=404)

        queryset = (
            CollateralAssetVerification.objects
            .select_related("company")
            .filter(company=company, del_flag=0)
            .order_by("-created_at")
        )

        items, meta = paginate_queryset(queryset, request)

        serializer = CollateralAssetVerificationDetailSerializer(
            items, many=True, context={"request": request}
        )

        return APIResponse.success(
            data={"items": serializer.data, "meta": meta},
            message="Collateral & asset verification fetched successfully."
        )

    # -----------------------------------------------------------------
    def post(self, request, company_id):

        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error("Company not found or access denied.", status_code=404)

        serializer = CollateralAssetVerificationSerializer(
            data=request.data,
            context={"company": company, "request": request}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():

            instance = serializer.save()

            application = create_or_get_application(request.user, company)

            update_step(
                application,
                step_id=SUB_STEP,
                completed=True,
                record_ids=[str(instance.id)]
            )

            update_step_status(application, MAIN_STEP)

        detail = CollateralAssetVerificationDetailSerializer(
            instance,
            context={"request": request}
        ).data

        return APIResponse.success(
            data=detail,
            message="Collateral & asset verification created successfully.",
            status_code=201
        )


# =====================================================================
# DETAIL / UPDATE / DELETE
# =====================================================================
class CollateralAssetVerificationDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # -----------------------------------------------------------------
    def get(self, request, company_id, record_id):

        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error("Company not found or access denied.", status_code=404)

        instance, error = get_object_or_error(
            CollateralAssetVerification.objects.select_related("company"),
            id=record_id,
            company=company,
            del_flag=0
        )
        if error:
            return error

        serializer = CollateralAssetVerificationDetailSerializer(instance, context={"request": request})

        return APIResponse.success(
            data=serializer.data,
            message="Record fetched successfully."
        )

    # -----------------------------------------------------------------
    def put(self, request, company_id, record_id):

        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error("Company not found or access denied.", status_code=404)

        instance, error = get_object_or_error(
            CollateralAssetVerification.objects,
            id=record_id,
            company=company,
            del_flag=0
        )
        if error:
            return error

        serializer = CollateralAssetVerificationSerializer(
            instance,
            data=request.data,
            partial=False,
            context={"company": company, "request": request}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():

            instance = serializer.save()

            application = create_or_get_application(request.user, company)

            update_step(
                application,
                step_id=SUB_STEP,
                completed=True,
                record_ids=[str(instance.id)]
            )

            update_step_status(application, MAIN_STEP)

        detail = CollateralAssetVerificationDetailSerializer(instance, context={"request": request}).data

        return APIResponse.success(
            data=detail,
            message="Record updated successfully."
        )

    # -----------------------------------------------------------------
    # PARTIAL UPDATE (PATCH)
    # -----------------------------------------------------------------
    def patch(self, request, company_id, record_id):

        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error("Company not found or access denied.", status_code=404)

        instance, error = get_object_or_error(
            CollateralAssetVerification.objects,
            id=record_id,
            company=company,
            del_flag=0
        )
        if error:
            return error

        serializer = CollateralAssetVerificationSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"company": company, "request": request}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():

            instance = serializer.save()

            application = create_or_get_application(request.user, company)

            update_step(
                application,
                step_id=SUB_STEP,
                completed=True,
                record_ids=[str(instance.id)]
            )

            update_step_status(application, MAIN_STEP)

        detail = CollateralAssetVerificationDetailSerializer(instance, context={"request": request}).data

        return APIResponse.success(
            data=detail,
            message="Record partially updated successfully."
        )

    # -----------------------------------------------------------------
    # DELETE
    # -----------------------------------------------------------------
    def delete(self, request, company_id, record_id):

        company = get_company_for_user(company_id, request.user)
        if not company:
            return APIResponse.error("Company not found or access denied.", status_code=404)

        instance, error = get_object_or_error(
            CollateralAssetVerification.objects,
            id=record_id,
            company=company,
            del_flag=0
        )
        if error:
            return error

        with transaction.atomic():

            instance.del_flag = 1
            instance.user_id_updated_by = request.user
            instance.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

            application = create_or_get_application(request.user, company)

            remaining = CollateralAssetVerification.objects.filter(company=company, del_flag=0).exists()

            update_step(
                application,
                step_id=SUB_STEP,
                completed=remaining,
                record_ids=[] if not remaining else None
            )

            update_step_status(application, MAIN_STEP)

        return APIResponse.success(
            message="Record deleted successfully."
        )
