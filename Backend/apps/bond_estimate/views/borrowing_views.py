
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from ..models.borrowing_details import BorrowingDetails, BorrowingType, RepaymentTerms
from ..serializers.borrowing_serializers import (
    BorrowingDetailsSerializer,
    BorrowingDetailsListSerializer,
    BorrowingDetailsCreateSerializer,
)
from ..mixins.borrowing_mixins import (
    SoftDeleteMixin,
    CompanyFilterMixin,
    BorrowingQueryOptimizationMixin,
    BulkOperationMixin,
    SearchFilterMixin,
    BorrowingSummaryMixin
)

from apps.bond_estimate.services.bond_estimation_service import (
    create_or_get_application,
    update_step
)

from ..models.BondEstimationApplicationModel import BondEstimationApplication

from config.common.response import APIResponse  # standard response wrapper



class BorrowingDetailsViewSet(
    SoftDeleteMixin,
    CompanyFilterMixin,
    BorrowingQueryOptimizationMixin,
    BulkOperationMixin,
    SearchFilterMixin,
    BorrowingSummaryMixin,
    viewsets.ModelViewSet
):
    """
    BORROWING DETAILS = STEP 2.1
    """

    queryset = BorrowingDetails.objects.all()
    permission_classes = [IsAuthenticated]
    ordering_fields = ['created_at', 'lender_amount', 'lender_name']
    ordering = ['-created_at']

    STEP_ID = "2.1"   # ⭐ VERY IMPORTANT

    # ---------------------------------------------------
    # SERIALIZER HANDLING
    # ---------------------------------------------------
    def get_serializer_class(self):
        if self.action == 'list':
            return BorrowingDetailsListSerializer
        elif self.action == 'create':
            return BorrowingDetailsCreateSerializer
        return BorrowingDetailsSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset

    # ---------------------------------------------------
    # STEP TRACKING (UNICORN LOGIC)
    # ---------------------------------------------------
    def _update_step_tracking(self, instance, is_delete=False):
        """
        Correct step-tracking for Borrowing Details (Step 2.1)
        Uses SAME format as FundPosition.
        """
        try:
            company = instance.company
            company_id = instance.company_id

            application = create_or_get_application(self.request.user, company)

            # Get active IDs
            active_ids = BorrowingDetails.objects.filter(
                company_id=company_id,
                is_del=0
            ).values_list("borrowing_id", flat=True)

            active_ids = [str(i) for i in active_ids]   # UUID SAFE

            if active_ids:
                update_step(
                    application=application,
                    step_id="2.1",
                    completed=True,
                    record_ids=active_ids,
                    metadata={
                        "total_borrowings": len(active_ids),
                        "last_action": "delete" if is_delete else "create/update",
                        "last_borrowing_id": str(instance.borrowing_id)
                    }
                )
            else:
                update_step(
                    application=application,
                    step_id="2.1",
                    completed=False,
                    record_ids=[],
                    metadata={
                        "total_borrowings": 0,
                        "last_action": "all_deleted"
                    }
                )

        except Exception as e:
            print("Borrowing Step Tracking Error:", str(e))

    # ---------------------------------------------------
    # LIST
    # ---------------------------------------------------
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page if page else queryset, many=True)

        if page:
            return self.get_paginated_response(serializer.data)

        return APIResponse.success(
            data=serializer.data,
            message="Borrowing details fetched successfully"
        )

    # ---------------------------------------------------
    # CREATE
    # ---------------------------------------------------
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = serializer.save()

        # Step Tracking
        self._update_step_tracking(instance)

        cache.delete(f'borrowing_summary_{instance.company_id}')

        return APIResponse.success(
            data=serializer.data,
            message="Borrowing created successfully",
            status_code=status.HTTP_201_CREATED
        )

    # ---------------------------------------------------
    # UPDATE
    # ---------------------------------------------------
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        updated_instance = serializer.save()

        # Step Tracking
        self._update_step_tracking(updated_instance)

        cache.delete(f'borrowing_summary_{instance.company_id}')

        return APIResponse.success(
            data=serializer.data,
            message="Borrowing updated successfully"
        )

    # ---------------------------------------------------
    # DELETE
    # ---------------------------------------------------
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Step Tracking (BEFORE deleting)
        self._update_step_tracking(instance, is_delete=True)

        company_id = instance.company_id

        self.perform_destroy(instance)

        cache.delete(f'borrowing_summary_{company_id}')

        return APIResponse.success(
            message="Borrowing deleted successfully"
        )

    # ---------------------------------------------------
    # BULK CREATE
    # ---------------------------------------------------
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def bulk_create(self, request):
        borrowings_data = request.data.get('borrowings', [])
        if not borrowings_data:
            return APIResponse.error(message="No borrowings data provided")

        serializer = BorrowingDetailsCreateSerializer(
            data=borrowings_data,
            many=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        instances = serializer.save()

        if instances:
            self._update_step_tracking(instances[0])

        return APIResponse.success(
            data=serializer.data,
            message=f"Successfully created {len(serializer.data)} borrowings",
            status_code=status.HTTP_201_CREATED
        )

    # ---------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------
    @action(detail=False, methods=['get'])
    def summary(self, request):
        company_id = request.query_params.get('company_id')
        if not company_id:
            return APIResponse.error(message="company_id is required")

        cache_key = f'borrowing_summary_{company_id}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return APIResponse.success(
                data=cached_data,
                message="Cached summary fetched"
            )

        response = super().get_summary(request)

        if response.status_code == 200:
            cache.set(cache_key, response.data, 300)

        return APIResponse.success(
            data=response.data,
            message="Borrowing summary fetched"
        )

    # ---------------------------------------------------
    # CHOICES
    # ---------------------------------------------------
    @action(detail=False, methods=['get'])
    def choices(self, request):
        borrowing_types = [
            {'value': c[0], 'label': c[1]} for c in BorrowingType.choices
        ]
        repayment_terms = [
            {'value': c[0], 'label': c[1]} for c in RepaymentTerms.choices
        ]

        return APIResponse.success(
            data={
                'borrowing_types': borrowing_types,
                'repayment_terms': repayment_terms
            },
            message="Dropdown choices fetched successfully"
        )

    # ---------------------------------------------------
    # RESTORE
    # ---------------------------------------------------
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        instance = self.get_object()

        if instance.is_del == 0:
            return APIResponse.error(message="Borrowing is not deleted")

        user_id = getattr(request.user, 'uuid', getattr(request.user, 'id', None))
        instance.restore(user_id=user_id)

        # Step Tracking
        self._update_step_tracking(instance)

        cache.delete(f'borrowing_summary_{instance.company_id}')

        serializer = self.get_serializer(instance)

        return APIResponse.success(
            data=serializer.data,
            message="Borrowing restored successfully"
        )

    # ---------------------------------------------------
    # COMPANY BORROWINGS
    # ---------------------------------------------------
    @action(detail=False, methods=['get'])
    def company_borrowings(self, request):
        company_id = request.query_params.get('company_id')

        if not company_id:
            return APIResponse.error(message="company_id is required")

        queryset = self.get_queryset().filter(company_id=company_id, is_del=0)

        serializer = BorrowingDetailsListSerializer(queryset, many=True)

        return APIResponse.success(
            data={
                'company_id': company_id,
                'count': queryset.count(),
                'borrowings': serializer.data
            },
            message="Company borrowings fetched successfully"
        )
    