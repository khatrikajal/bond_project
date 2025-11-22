# apps/bond_estimate/views/credit_rating_views.py

import logging
from datetime import date
from django.db import transaction
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action

from apps.bond_estimate.mixins.ApplicationScopedMixin import ApplicationScopedMixin
from apps.bond_estimate.models.CreditRatingDetailsModel import CreditRatingDetails
from apps.bond_estimate.serializers.CreditRatingSerializer import (
    CreditRatingSerializer,
    CreditRatingListSerializer,
)
from apps.bond_estimate.models.AgencyRatingChoice import RatingAgency, CreditRating
from config.common.response import APIResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CreditRatingViewSet(ApplicationScopedMixin, viewsets.ViewSet):
    """
    STEP 1.2 — CREDIT RATING API
    URL: /api/bond_estimate/applications/<application_id>/credit-ratings/
    """

    permission_classes = [IsAuthenticated]
    STEP_ID = "1.2"

    # Queryset for company
    def get_queryset(self):
        return CreditRatingDetails.objects.filter(
            company=self.application.company,
            is_del=0
        ).order_by("-created_at")

    # STEP update logic
    def _mark_step(self):
        active_ids = list(self.get_queryset().values_list("credit_rating_id", flat=True))

        self.application.mark_step(
            step_id=self.STEP_ID,
            completed=bool(active_ids),
            record_ids=[str(i) for i in active_ids]
        )

    # ---------------------- LIST ----------------------
    def list(self, request, application_id):
        logger.info(f"[CreditRating] LIST for application {application_id}")

        queryset = self.get_queryset()

        # Auto-update expired record status
        today = date.today()
        for rating in queryset:
            if rating.valid_till < today and rating.reting_status:
                rating.reting_status = False
                rating.save(update_fields=["reting_status", "updated_at"])

        serializer = CreditRatingListSerializer(queryset, many=True, context={"request": request})

        self._mark_step()

        return APIResponse.success(
            message="Credit ratings fetched successfully",
            data=serializer.data
        )

    # ---------------------- CREATE ----------------------
    @transaction.atomic
    def create(self, request, application_id):
        logger.info(f"[CreditRating] CREATE for application {application_id}")

        serializer = CreditRatingSerializer(
            data=request.data,
            context={"request": request, "company_id": str(self.application.company.company_id)}
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save()

        self._mark_step()

        return APIResponse.success(
            message="Credit rating created successfully",
            data=CreditRatingListSerializer(instance, context={"request": request}).data,
            status_code=201
        )

    # ---------------------- UPDATE (PATCH) ----------------------
    @transaction.atomic
    def partial_update(self, request, application_id, pk):
        rating = self._get_object(pk)

        serializer = CreditRatingSerializer(
            rating, data=request.data, partial=True,
            context={"request": request, "company_id": str(self.application.company.company_id), "instance": rating}
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()

        self._mark_step()

        return APIResponse.success(
            message="Credit rating updated successfully",
            data=CreditRatingListSerializer(updated, context={"request": request}).data
        )

    # ---------------------- DELETE ----------------------
    @transaction.atomic
    def destroy(self, request, application_id, pk):
        rating = self._get_object(pk)
        rating.is_del = 1
        rating.user_id_updated_by = request.user
        rating.save(update_fields=["is_del", "user_id_updated_by", "updated_at"])

        self._mark_step()

        return APIResponse.success(
            message="Credit rating deleted successfully",
            data={"deleted_id": pk}
        )

    # ---------------------- Object fetch ----------------------
    def _get_object(self, pk):
        return CreditRatingDetails.objects.get(
            credit_rating_id=pk,
            company=self.application.company,
            is_del=0
        )

    # ---------------------- Choices Public ----------------------
    @action(detail=False, methods=["get"], url_path="choices",
            permission_classes=[AllowAny], authentication_classes=[])
    def choices(self, request, application_id=None):
        return APIResponse.success(
            message="Rating options fetched",
            data={
                "agencies": [{"value": v, "label": l} for v, l in RatingAgency.choices],
                "ratings": [{"value": v, "label": l} for v, l in CreditRating.choices]
            }
        )
