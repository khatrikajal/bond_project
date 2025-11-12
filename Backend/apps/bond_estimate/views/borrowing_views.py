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
from ..models.BondEstimationApplicationModel import BondEstimationApplication
from config.common.response import APIResponse  # ✅ Import your standardized response helper


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
    ViewSet for Borrowing Details (Step 2)
    """
    queryset = BorrowingDetails.objects.all()
    permission_classes = []
    ordering_fields = ['created_at', 'lender_amount', 'lender_name']
    ordering = ['-created_at']
    STEP_ID = "2"

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

    # ---------------- Utility Methods ----------------
    def _get_application(self, company_id):
        try:
            application = BondEstimationApplication.objects.get(
                company_id=company_id,
                user=self.request.user,
                status__in=['DRAFT', 'IN_PROGRESS']
            )
        except BondEstimationApplication.DoesNotExist:
            from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
            company = get_object_or_404(CompanyInformation, company_id=company_id)
            application = BondEstimationApplication.objects.create(
                user=self.request.user,
                company=company,
                status='IN_PROGRESS'
            )
        return application

    def _update_step_tracking(self, borrowing_instance, is_delete=False):
        try:
            application = self._get_application(borrowing_instance.company_id)
            active_borrowings = BorrowingDetails.objects.filter(
                company_id=borrowing_instance.company_id,
                is_del=0
            ).count()

            if active_borrowings > 0:
                application.mark_step(
                    self.STEP_ID,
                    completed=True,
                    metadata={
                        'total_borrowings': active_borrowings,
                        'last_action': 'delete' if is_delete else 'create/update',
                        'last_borrowing_id': str(borrowing_instance.borrowing_id)
                    }
                )
                application.last_accessed_step = 2
                application.save(update_fields=['last_accessed_step'])
            else:
                application.mark_step(
                    self.STEP_ID,
                    completed=False,
                    metadata={'total_borrowings': 0, 'last_action': 'all_deleted'}
                )
        except Exception as e:
            print(f"Step tracking error: {str(e)}")

    # ---------------- CRUD Operations ----------------
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

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self._update_step_tracking(instance)
        company_id = serializer.validated_data.get('company_id')
        if company_id:
            cache.delete(f'borrowing_summary_{company_id}')
        return APIResponse.success(
            data=serializer.data,
            message="Borrowing created successfully",
            status_code=status.HTTP_201_CREATED
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        self._update_step_tracking(updated_instance)
        cache.delete(f'borrowing_summary_{instance.company_id}')
        return APIResponse.success(
            data=serializer.data,
            message="Borrowing updated successfully"
        )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        company_id = instance.company_id
        self._update_step_tracking(instance, is_delete=True)
        self.perform_destroy(instance)
        cache.delete(f'borrowing_summary_{company_id}')
        return APIResponse.success(
            message="Borrowing deleted successfully"
        )

    # ---------------- Custom Actions ----------------
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def bulk_create(self, request):
        borrowings_data = request.data.get('borrowings', [])
        if not borrowings_data:
            return APIResponse.error(message="No borrowings data provided")
        serializer = BorrowingDetailsCreateSerializer(data=borrowings_data, many=True, context={'request': request})
        if serializer.is_valid():
            instances = serializer.save()
            if instances:
                self._update_step_tracking(instances[0])
            return APIResponse.success(
                data=serializer.data,
                message=f"Successfully created {len(serializer.data)} borrowings",
                status_code=status.HTTP_201_CREATED
            )
        return APIResponse.error(message="Validation error", errors=serializer.errors)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        company_id = request.query_params.get('company_id')
        if not company_id:
            return APIResponse.error(message="company_id is required")
        cache_key = f'borrowing_summary_{company_id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return APIResponse.success(data=cached_data, message="Cached summary fetched")
        response = super().get_summary(request)
        if response.status_code == 200:
            cache.set(cache_key, response.data, 300)
        return APIResponse.success(data=response.data, message="Borrowing summary fetched")

    @action(detail=False, methods=['get'])
    def choices(self, request):
        borrowing_types = [{'value': c[0], 'label': c[1]} for c in BorrowingType.choices]
        repayment_terms = [{'value': c[0], 'label': c[1]} for c in RepaymentTerms.choices]
        return APIResponse.success(
            data={'borrowing_types': borrowing_types, 'repayment_terms': repayment_terms},
            message="Dropdown choices fetched successfully"
        )

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        instance = self.get_object()
        if instance.is_del == 0:
            return APIResponse.error(message="Borrowing is not deleted")
        user_id = getattr(request.user, 'uuid', getattr(request.user, 'id', None))
        instance.restore(user_id=user_id)
        self._update_step_tracking(instance)
        cache.delete(f'borrowing_summary_{instance.company_id}')
        serializer = self.get_serializer(instance)
        return APIResponse.success(
            data=serializer.data,
            message="Borrowing restored successfully"
        )

    @action(detail=False, methods=['get'])
    def company_borrowings(self, request):
        company_id = request.query_params.get('company_id')
        if not company_id:
            return APIResponse.error(message="company_id is required")
        queryset = self.get_queryset().filter(company_id=company_id, is_del=0)
        serializer = BorrowingDetailsListSerializer(queryset, many=True)
        return APIResponse.success(
            data={'company_id': company_id, 'count': queryset.count(), 'borrowings': serializer.data},
            message="Company borrowings fetched successfully"
        )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def mark_step_complete(self, request):
        company_id = request.data.get('company_id')
        if not company_id:
            return APIResponse.error(message="company_id is required")
        application = self._get_application(company_id)
        borrowings_count = self.get_queryset().filter(company_id=company_id, is_del=0).count()
        application.mark_step(
            self.STEP_ID,
            completed=True,
            metadata={'total_borrowings': borrowings_count, 'completed_manually': True}
        )
        return APIResponse.success(
            data={'application_id': str(application.application_id), 'borrowings_count': borrowings_count},
            message="Step 2 marked as complete"
        )

    @action(detail=False, methods=['get'])
    def step_status(self, request):
        company_id = request.query_params.get('company_id')
        if not company_id:
            return APIResponse.error(message="company_id is required")
        try:
            application = BondEstimationApplication.objects.get(
                company_id=company_id,
                user=request.user,
                status__in=['DRAFT', 'IN_PROGRESS', 'READY_FOR_CALCULATION', 'COMPLETED']
            )
        except BondEstimationApplication.DoesNotExist:
            return APIResponse.success(
                data={'step_2_completed': False, 'borrowings_count': 0},
                message="No bond estimation application found"
            )
        step_state = application.get_step_state(self.STEP_ID)
        borrowings_count = self.get_queryset().filter(company_id=company_id, is_del=0).count()
        return APIResponse.success(
            data={
                'step_2_completed': step_state.get('completed', False),
                'borrowings_count': borrowings_count,
                'last_updated': step_state.get('updated_at'),
                'application_id': str(application.application_id),
                'application_status': application.status,
                'metadata': step_state.get('metadata', {})
            },
            message="Step 2 status fetched successfully"
        )
