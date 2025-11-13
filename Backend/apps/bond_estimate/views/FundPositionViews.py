from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Sum, Count
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.bond_estimate.models.FundPositionModel import FundPosition
from apps.bond_estimate.serializers.FundPositionSerializer import (
    FundPositionSerializer,
    FundPositionListSerializer,
)
from apps.bond_estimate.services.bond_estimation_service import (
    create_or_get_application,
    update_step,
)
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from config.common.response import APIResponse


# ============================================================
#                LIST + CREATE FUND POSITIONS
# ============================================================
class FundPositionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List all fund positions",
        parameters=[
            OpenApiParameter(
                name="company_id",
                description="Company UUID",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(name="from_date", type=str, required=False),
            OpenApiParameter(name="to_date", type=str, required=False),
        ],
        responses={200: FundPositionListSerializer(many=True)},
        tags=["Bond Estimate - Fund Position"],
    )
    def get(self, request):
        company_id = request.query_params.get("company_id")
        if not company_id:
            return APIResponse.error("company_id is required", 400)

        try:
            CompanyInformation.objects.get(pk=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error("Company not found", 404)

        qs = FundPosition.objects.filter(company_id=company_id, del_flag=0)

        if request.query_params.get("from_date"):
            qs = qs.filter(
                Q(cash_balance_date__gte=request.query_params["from_date"])
                | Q(bank_balance_date__gte=request.query_params["from_date"])
            )
        if request.query_params.get("to_date"):
            qs = qs.filter(
                Q(cash_balance_date__lte=request.query_params["to_date"])
                | Q(bank_balance_date__lte=request.query_params["to_date"])
            )

        stats = qs.aggregate(
            total_records=Count("fund_position_id"),
            total_cash=Sum("cash_balance_amount"),
            total_bank=Sum("bank_balance_amount"),
        )

        serializer = FundPositionListSerializer(qs, many=True)

        return APIResponse.success(
            {
                "records": serializer.data,
                "stats": {
                    "total_records": stats["total_records"] or 0,
                    "total_cash_balance": str(stats["total_cash"] or 0),
                    "total_bank_balance": str(stats["total_bank"] or 0),
                },
            },
            "Fund positions fetched successfully",
        )

    @extend_schema(
        summary="Create fund position",
        request=FundPositionSerializer,
        responses={201: FundPositionSerializer},
        tags=["Bond Estimate - Fund Position"],
    )
    @transaction.atomic
    def post(self, request):
        company_id = request.data.get("company_id")
        if not company_id:
            return APIResponse.error("company_id is required", 400)

        try:
            company = CompanyInformation.objects.get(pk=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error("Company not found", 404)

        serializer = FundPositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fund_position = FundPosition.objects.create(
            company_id=company_id,
            cash_balance_date=serializer.validated_data["cash_balance_date"],
            bank_balance_date=serializer.validated_data["bank_balance_date"],
            cash_balance_amount=serializer.validated_data["cash_balance_amount"],
            bank_balance_amount=serializer.validated_data["bank_balance_amount"],
            remarks=serializer.validated_data.get("remarks"),
            user_id_updated_by=request.user,
        )

        application = create_or_get_application(request.user, company)

        update_step(
            application=application,
            step_id="1.1",
            completed=True,
            record_ids=[str(fund_position.fund_position_id)],
            metadata={
                "cash_balance": str(fund_position.cash_balance_amount),
                "bank_balance": str(fund_position.bank_balance_amount),
                "total_balance": str(fund_position.total_balance),
            },
        )

        return APIResponse.success(
            FundPositionSerializer(fund_position).data,
            "Fund position created successfully",
            201,
        )


# ============================================================
#                FUND POSITION DETAIL VIEW
# ============================================================
class FundPositionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return FundPosition.objects.get(pk=pk, del_flag=0)
        except FundPosition.DoesNotExist:
            return None

    # ============================================================
    # GET SINGLE RECORD
    # ============================================================
    @extend_schema(
        summary="Get fund position details",
        responses={200: FundPositionSerializer},
        tags=["Bond Estimate - Fund Position"],
    )
    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return APIResponse.error("Fund position not found", 404)

        return APIResponse.success(
            FundPositionSerializer(obj).data,
            "Fund position fetched successfully",
        )

    # ============================================================
    # UPDATE FUND POSITION
    # ============================================================
    @extend_schema(
        summary="Update fund position",
        request=FundPositionSerializer,
        responses={200: FundPositionSerializer},
        tags=["Bond Estimate - Fund Position"],
    )
    @transaction.atomic
    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return APIResponse.error("Fund position not found", 404)

        serializer = FundPositionSerializer(obj, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        # Apply updated fields
        for field in [
            "cash_balance_date",
            "bank_balance_date",
            "cash_balance_amount",
            "bank_balance_amount",
            "remarks",
        ]:
            setattr(obj, field, serializer.validated_data.get(field))

        obj.user_id_updated_by = request.user
        obj.save()

        # Step update
        application = create_or_get_application(request.user, obj.company)

        update_step(
            application=application,
            step_id="1.1",
            completed=True,
            record_ids=[str(obj.fund_position_id)],
            metadata={"last_updated": obj.updated_at.isoformat()},
        )

        return APIResponse.success(
            FundPositionSerializer(obj).data,
            "Fund position updated successfully",
        )

    # ============================================================
    # DELETE FUND POSITION (SOFT DELETE)
    # ============================================================
    @extend_schema(summary="Delete fund position", tags=["Bond Estimate - Fund Position"])
    @transaction.atomic
    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return APIResponse.error("Fund position not found", 404)

        # Soft delete
        obj.del_flag = 1
        obj.user_id_updated_by = request.user
        obj.save()

        # Remaining fund positions
        remaining = FundPosition.objects.filter(
            company=obj.company, del_flag=0
        ).values_list("fund_position_id", flat=True)

        application = create_or_get_application(request.user, obj.company)

        if remaining:
            # Convert UUID → string (IMPORTANT)
            record_ids = [str(rid) for rid in remaining]

            update_step(
                application=application,
                step_id="1.1",
                completed=True,
                record_ids=record_ids,
            )
        else:
            update_step(
                application=application,
                step_id="1.1",
                completed=False,
                record_ids=[],
            )

        return APIResponse.success(
            {"deleted_id": str(pk)},
            "Fund position deleted successfully",
        )

# ============================================================
#                BULK CREATE
# ============================================================
class FundPositionBulkView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Bulk create fund positions",
        request=FundPositionSerializer(many=True),
        responses={201: FundPositionSerializer(many=True)},
        tags=["Bond Estimate - Fund Position"],
    )
    @transaction.atomic
    def post(self, request):
        data = request.data
        if not isinstance(data, list) or len(data) == 0:
            return APIResponse.error("Payload must be a non-empty list", 400)

        company_id = data[0].get("company_id")
        if not company_id:
            return APIResponse.error("company_id is required", 400)

        try:
            company = CompanyInformation.objects.get(pk=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error("Company not found", 404)

        serializer = FundPositionSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)

        created_objects = []

        for item in serializer.validated_data:
            obj = FundPosition.objects.create(
                company_id=company_id,
                cash_balance_date=item["cash_balance_date"],
                bank_balance_date=item["bank_balance_date"],
                cash_balance_amount=item["cash_balance_amount"],
                bank_balance_amount=item["bank_balance_amount"],
                remarks=item.get("remarks"),
                user_id_updated_by=request.user,
            )
            created_objects.append(obj)

        record_ids = [str(obj.fund_position_id) for obj in created_objects]

        application = create_or_get_application(request.user, company)

        update_step(
            application=application,
            step_id="1.1",
            completed=True,
            record_ids=record_ids,
            metadata={"bulk_created": len(record_ids)},
        )

        return APIResponse.success(
            FundPositionSerializer(created_objects, many=True).data,
            f"{len(record_ids)} fund positions created successfully",
            201,
        )
