from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.db import transaction
import logging

from config.common.response import APIResponse
from apps.bond_estimate.mixins.ApplicationScopedMixin import ApplicationScopedMixin

from apps.bond_estimate.models.borrowing_details import BorrowingDetails, BorrowingType, RepaymentTerms
from apps.bond_estimate.serializers.borrowing_serializers import (
    BorrowingDetailsSerializer,
    BorrowingDetailsCreateSerializer,
    BorrowingDetailsListSerializer
)

# -------------------------------------------------------
# LOGGER
# -------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BorrowingDetailsViewSet(ApplicationScopedMixin, viewsets.ModelViewSet):
    """
    Borrowing Details for a specific BondEstimationApplication
    URL -> /applications/<application_id>/borrowings/
    """
    permission_classes = [IsAuthenticated]
    lookup_field = "borrowing_id"

    STEP_ID = "3.1"

    # -------------------------------------------------------
    # QUERYSET
    # -------------------------------------------------------
    def get_queryset(self):
        logger.debug(f"[BorrowingDetails] Fetching queryset for application: {self.application.application_id}")
        return BorrowingDetails.objects.filter(
            application=self.application,
            is_del=0
        ).order_by("-created_at")

    # -------------------------------------------------------
    # SERIALIZER SELECTION
    # -------------------------------------------------------
    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingDetailsListSerializer
        elif self.action == "create":
            return BorrowingDetailsCreateSerializer
        return BorrowingDetailsSerializer

    # -------------------------------------------------------
    # STEP MARKING (UUID → STRING)
    # -------------------------------------------------------
    def _mark_step(self):
        active_ids = BorrowingDetails.objects.filter(
            application=self.application,
            is_del=0
        ).values_list("borrowing_id", flat=True)

        active_ids = [str(pk) for pk in active_ids]  # fix for JSON serialization

        logger.debug(f"[BorrowingDetails] Marking step {self.STEP_ID} → Active IDs: {active_ids}")

        self.application.mark_step(
            self.STEP_ID,
            completed=bool(active_ids),
            record_ids=active_ids
        )

    # -------------------------------------------------------
    # LIST
    # -------------------------------------------------------
    def list(self, request, application_id, *args, **kwargs):
        logger.info(f"[BorrowingDetails] LIST called for application {application_id}")

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return APIResponse.success(
            message="Borrowing details fetched successfully",
            data=serializer.data
        )

    # -------------------------------------------------------
    # RETRIEVE
    # -------------------------------------------------------
    def retrieve(self, request, application_id, *args, **kwargs):
        logger.info(f"[BorrowingDetails] RETRIEVE for application {application_id}")

        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return APIResponse.success(
            message="Borrowing details fetched successfully",
            data=serializer.data
        )

    # -------------------------------------------------------
    # CREATE (UPDATED RESPONSE FORMAT)
    # -------------------------------------------------------
    @transaction.atomic
    def create(self, request, application_id, *args, **kwargs):
        logger.info(f"[BorrowingDetails] CREATE requested for application {application_id} | Data: {request.data}")

        data = request.data.copy()
        data["application"] = self.application.application_id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(
            application=self.application,
            user_id_updated_by=request.user.id
        )

        logger.debug(f"[BorrowingDetails] Created borrowing ID: {instance.borrowing_id}")

        self._mark_step()

        # ------------------------------
        # RESPONSE YOU REQUESTED
        # ------------------------------
        response_data = {
            "borrowing_id": str(instance.borrowing_id),
            
            "lender_name": instance.lender_name,
            "lender_amount": str(instance.lender_amount),
            "borrowing_type": instance.borrowing_type,
            "repayment_terms": instance.repayment_terms,
            "monthly_principal_payment": str(instance.monthly_principal_payment),
            "interest_payment_percentage": str(instance.interest_payment_percentage),
            "monthly_interest_payment": str(instance.monthly_interest_payment),
        }

        return APIResponse.success(
            message="Borrowing created successfully",
            data=response_data,
            status_code=201
        )

    # -------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------
    @transaction.atomic
    def update(self, request, application_id, *args, **kwargs):
        logger.info(f"[BorrowingDetails] UPDATE for application {application_id} | Data: {request.data}")

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user_id_updated_by=request.user.id)

        self._mark_step()

        logger.debug(f"[BorrowingDetails] Updated borrowing ID: {instance.borrowing_id}")

        return APIResponse.success(
            message="Borrowing updated successfully",
            data=serializer.data
        )

    # -------------------------------------------------------
    # PARTIAL UPDATE
    # -------------------------------------------------------
    @transaction.atomic
    def partial_update(self, request, application_id, *args, **kwargs):
        logger.info(f"[BorrowingDetails] PATCH for application {application_id} | Data: {request.data}")

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user_id_updated_by=request.user.id)

        self._mark_step()

        logger.debug(f"[BorrowingDetails] Partially updated borrowing ID: {instance.borrowing_id}")

        return APIResponse.success(
            message="Borrowing updated successfully",
            data=serializer.data
        )

    # -------------------------------------------------------
    # DELETE (SOFT DELETE)
    # -------------------------------------------------------
    @transaction.atomic
    def destroy(self, request, application_id, *args, **kwargs):
        logger.warning(f"[BorrowingDetails] DELETE for application {application_id}")

        instance = self.get_object()
        instance.is_del = 1
        instance.user_id_updated_by = request.user.id
        instance.save()

        self._mark_step()

        logger.debug(f"[BorrowingDetails] Soft delete borrowing ID: {instance.borrowing_id}")

        return APIResponse.success(
            message="Borrowing deleted successfully",
            data={"deleted_id": str(instance.borrowing_id)}
        )

    # -------------------------------------------------------
    # CHOICES
    # -------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="choices",permission_classes=[],authentication_classes=[])
    def choices(self, request, application_id=None):
        logger.info("[BorrowingDetails] Fetching dropdown choices")

        borrowing_types = [{"value": v, "label": l} for v, l in BorrowingType.choices]
        repayment_terms = [{"value": v, "label": l} for v, l in RepaymentTerms.choices]

        return APIResponse.success(
            message="Borrowing choices fetched",
            data={
                "borrowing_types": borrowing_types,
                "repayment_terms": repayment_terms
            }
        )
