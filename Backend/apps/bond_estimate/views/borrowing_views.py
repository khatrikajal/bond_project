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
    BorrowingTypeChoiceSerializer,
    RepaymentTermsChoiceSerializer
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
    ViewSet for Borrowing Details - Step 2 of Bond Estimation
    
    Provides CRUD operations with:
    - Soft delete functionality
    - Company filtering
    - Query optimization
    - Bulk operations
    - Search and filter
    - Summary statistics
    - Step tracking for bond estimation workflow
    
    Endpoints:
    - GET /api/borrowing/ - List all borrowings
    - POST /api/borrowing/ - Create new borrowing
    - GET /api/borrowing/{id}/ - Retrieve specific borrowing
    - PUT /api/borrowing/{id}/ - Update borrowing
    - PATCH /api/borrowing/{id}/ - Partial update
    - DELETE /api/borrowing/{id}/ - Soft delete borrowing
    - POST /api/borrowing/bulk_delete/ - Bulk delete
    - POST /api/borrowing/bulk_restore/ - Bulk restore
    - GET /api/borrowing/summary/ - Get summary statistics
    - GET /api/borrowing/choices/ - Get dropdown choices
    - POST /api/borrowing/mark_step_complete/ - Mark step 2 as complete
    - GET /api/borrowing/step_status/ - Get step 2 status
    """
    
    queryset = BorrowingDetails.objects.all()
    # permission_classes = [IsAuthenticated]
    permission_classes = []  # Temporarily disabled for testing
    # Optimize ordering for index usage
    ordering_fields = ['created_at', 'lender_amount', 'lender_name']
    ordering = ['-created_at']
    
    # Step configuration
    STEP_ID = "2"  # Step 2: Borrowing Details
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        Optimizes performance for different operations
        """
        if self.action == 'list':
            return BorrowingDetailsListSerializer
        elif self.action == 'create':
            return BorrowingDetailsCreateSerializer
        return BorrowingDetailsSerializer

    def get_queryset(self):
        """
        Optimized queryset with proper filtering
        Uses database indexes for performance
        """
        queryset = super().get_queryset()
        
        # Apply ordering
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset

    def _get_application(self, company_id):
        """Helper to get or create bond estimation application"""
        try:
            application = BondEstimationApplication.objects.get(
                company_id=company_id,
                user=self.request.user,
                status__in=['DRAFT', 'IN_PROGRESS']
            )
        except BondEstimationApplication.DoesNotExist:
            # Auto-create if doesn't exist
            from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
            company = get_object_or_404(CompanyInformation, company_id=company_id)
            application = BondEstimationApplication.objects.create(
                user=self.request.user,
                company=company,
                status='IN_PROGRESS'
            )
        return application

    def _update_step_tracking(self, borrowing_instance, is_delete=False):
        """
        Update step tracking after borrowing operations
        Automatically marks Step 2 as complete when borrowings exist
        """
        try:
            application = self._get_application(borrowing_instance.company_id)
            
            # Count active borrowings for this company
            active_borrowings = BorrowingDetails.objects.filter(
                company_id=borrowing_instance.company_id,
                is_del=0
            ).count()
            
            if active_borrowings > 0:
                # Mark Step 2 as complete since borrowings exist
                application.mark_step(
                    self.STEP_ID,
                    completed=True,
                    metadata={
                        'total_borrowings': active_borrowings,
                        'last_action': 'delete' if is_delete else 'create/update',
                        'last_borrowing_id': str(borrowing_instance.borrowing_id)
                    }
                )
                
                # Update last accessed step
                application.last_accessed_step = 2
                application.save(update_fields=['last_accessed_step'])
            else:
                # No borrowings left, mark as incomplete
                application.mark_step(
                    self.STEP_ID,
                    completed=False,
                    metadata={
                        'total_borrowings': 0,
                        'last_action': 'all_deleted'
                    }
                )
                
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Step tracking error: {str(e)}")

    def list(self, request, *args, **kwargs):
        """
        List borrowings with pagination and filtering
        Supports query parameters:
        - company_id: Filter by company
        - search: Search by lender name
        - borrowing_type: Filter by type
        - repayment_terms: Filter by terms
        - min_amount, max_amount: Amount range
        - start_date, end_date: Date range
        - page, page_size: Pagination
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create new borrowing detail
        Uses transaction to ensure data consistency
        Automatically updates step tracking
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Update step tracking
        self._update_step_tracking(instance)
        
        # Clear cache for this company
        company_id = serializer.validated_data.get('company_id')
        if company_id:
            cache.delete(f'borrowing_summary_{company_id}')
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Update borrowing detail
        Uses transaction for data consistency
        Updates step tracking
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        
        # Update step tracking
        self._update_step_tracking(updated_instance)
        
        # Clear cache
        cache.delete(f'borrowing_summary_{instance.company_id}')
        
        return Response(serializer.data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete borrowing detail
        Updates step tracking to reflect deletion
        """
        instance = self.get_object()
        company_id = instance.company_id
        
        # Update step tracking before delete
        self._update_step_tracking(instance, is_delete=True)
        
        self.perform_destroy(instance)
        
        # Clear cache
        cache.delete(f'borrowing_summary_{company_id}')
        
        return Response(
            {'message': 'Borrowing deleted successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def bulk_create(self, request):
        """
        Bulk create multiple borrowing records
        Expects: {"borrowings": [{...}, {...}], "company_id": "uuid"}
        Automatically marks Step 2 as complete
        """
        borrowings_data = request.data.get('borrowings', [])
        company_id = request.data.get('company_id')
        
        if not borrowings_data:
            return Response(
                {'error': 'No borrowings data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = BorrowingDetailsCreateSerializer(
            data=borrowings_data,
            many=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            instances = serializer.save()
            
            # Update step tracking (just once for all instances)
            if instances:
                self._update_step_tracking(instances[0])
            
            # Clear cache for affected companies
            company_ids = set(item['company_id'] for item in borrowings_data)
            for cid in company_ids:
                cache.delete(f'borrowing_summary_{cid}')
            
            return Response(
                {
                    'message': f'Successfully created {len(serializer.data)} borrowings',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk soft delete - inherited from BulkOperationMixin"""
        return super().bulk_delete(request)

    @action(detail=False, methods=['post'])
    def bulk_restore(self, request):
        """Bulk restore - inherited from BulkOperationMixin"""
        return super().bulk_restore(request)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get borrowing summary - inherited from BorrowingSummaryMixin
        Supports caching for performance
        """
        company_id = request.query_params.get('company_id')
        
        if not company_id:
            return Response(
                {'error': 'company_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check cache first
        cache_key = f'borrowing_summary_{company_id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)
        
        # Get fresh data
        response = super().get_summary(request)
        
        # Cache for 5 minutes
        if response.status_code == 200:
            cache.set(cache_key, response.data, 300)
        
        return response

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """
        Get dropdown choices for borrowing types and repayment terms
        Returns data formatted for frontend dropdowns
        """
        borrowing_types = [
            {'value': choice[0], 'label': choice[1]}
            for choice in BorrowingType.choices
        ]
        
        repayment_terms = [
            {'value': choice[0], 'label': choice[1]}
            for choice in RepaymentTerms.choices
        ]
        
        return Response({
            'borrowing_types': borrowing_types,
            'repayment_terms': repayment_terms
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restore a single soft-deleted borrowing
        pk should be a UUID
        """
        instance = self.get_object()
        
        if instance.is_del == 0:
            return Response(
                {'error': 'Borrowing is not deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'uuid'):
                user_id = request.user.uuid
            else:
                user_id = request.user.id
        
        instance.restore(user_id=user_id)
        
        # Update step tracking
        self._update_step_tracking(instance)
        
        # Clear cache
        cache.delete(f'borrowing_summary_{instance.company_id}')
        
        serializer = self.get_serializer(instance)
        return Response(
            {
                'message': 'Borrowing restored successfully',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def company_borrowings(self, request):
        """
        Get all borrowings for a specific company
        Optimized endpoint for company-specific data
        """
        company_id = request.query_params.get('company_id')
        
        if not company_id:
            return Response(
                {'error': 'company_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            company_id=company_id,
            is_del=0
        )
        
        serializer = BorrowingDetailsListSerializer(queryset, many=True)
        
        return Response({
            'company_id': company_id,
            'count': queryset.count(),
            'borrowings': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def mark_step_complete(self, request):
        """
        Manually mark Step 2 (Borrowing Details) as complete
        
        Request body:
        {
            "company_id": "uuid",
            "force_complete": false  # Optional: force complete even if no borrowings exist
        }
        
        Response:
        {
            "message": "Step 2 marked as complete",
            "step_status": {...}
        }
        """
        company_id = request.data.get('company_id')
        force_complete = request.data.get('force_complete', False)
        
        if not company_id:
            return Response(
                {'error': 'company_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get application
        application = self._get_application(company_id)
        
        # Check if there are any borrowings
        borrowings_count = self.get_queryset().filter(
            company_id=company_id,
            is_del=0
        ).count()
        
        if borrowings_count == 0 and not force_complete:
            return Response(
                {
                    'error': 'No borrowings found for this company',
                    'message': 'Please add at least one borrowing record or use force_complete=true'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark step as complete
        application.mark_step(
            self.STEP_ID,
            completed=True,
            metadata={
                'total_borrowings': borrowings_count,
                'completed_manually': True,
                'force_completed': force_complete
            }
        )
        
        # Get updated step status
        step_status = application.get_step_state(self.STEP_ID)
        
        return Response({
            'message': 'Step 2 (Borrowing Details) marked as complete',
            'application_id': str(application.application_id),
            'step_status': step_status,
            'borrowings_count': borrowings_count
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def step_status(self, request):
        """
        Get Step 2 completion status
        
        Query params:
        - company_id: UUID (required)
        
        Response:
        {
            "step_2_completed": true/false,
            "borrowings_count": 5,
            "last_updated": "timestamp"
        }
        """
        company_id = request.query_params.get('company_id')
        
        if not company_id:
            return Response(
                {'error': 'company_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            application = BondEstimationApplication.objects.get(
                company_id=company_id,
                user=request.user,
                status__in=['DRAFT', 'IN_PROGRESS', 'READY_FOR_CALCULATION', 'COMPLETED']
            )
        except BondEstimationApplication.DoesNotExist:
            return Response({
                'step_2_completed': False,
                'borrowings_count': 0,
                'message': 'No bond estimation application found'
            }, status=status.HTTP_200_OK)
        
        # Get step state
        step_state = application.get_step_state(self.STEP_ID)
        
        # Count borrowings
        borrowings_count = self.get_queryset().filter(
            company_id=company_id,
            is_del=0
        ).count()
        
        return Response({
            'step_2_completed': step_state.get('completed', False),
            'borrowings_count': borrowings_count,
            'last_updated': step_state.get('updated_at'),
            'application_id': str(application.application_id),
            'application_status': application.status,
            'metadata': step_state.get('metadata', {})
        }, status=status.HTTP_200_OK)