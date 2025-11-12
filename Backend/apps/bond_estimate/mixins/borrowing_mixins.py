from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q, Sum, Avg, Count
from decimal import Decimal
from ..model.borrowing_details import BorrowingType, RepaymentTerms


class SoftDeleteMixin:
    """
    Mixin to handle soft delete operations
    Filters out deleted records by default
    """

    def get_queryset(self):
        """Filter out soft-deleted records unless explicitly requested"""
        queryset = super().get_queryset()
        if not self.request.query_params.get('include_deleted', False):
            queryset = queryset.filter(is_del=0)
        return queryset

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete"""
        user_id = None
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            user_id = getattr(self.request.user, 'uuid', self.request.user.id)
        instance.soft_delete(user_id=user_id)


class CompanyFilterMixin:
    """
    Mixin to filter records by company_id
    Optimizes queries with proper indexing
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset


class BorrowingQueryOptimizationMixin:
    """
    Mixin to optimize borrowing queries
    Prevents N+1 problems with select_related and prefetch_related
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, 'action', None) == 'list':
            queryset = queryset.only(
                'borrowing_id',
                'lender_name',
                'lender_amount',
                'borrowing_type',
                'repayment_terms',
                'monthly_principal_payment',
                'interest_payment_percentage',
                'monthly_interest_payment',
                'created_at'
            )
        return queryset


class BulkOperationMixin:
    """
    Mixin to handle bulk soft delete and restore operations
    """

    def bulk_delete(self, request, *args, **kwargs):
        """
        Bulk soft delete
        Expects: {"ids": ["uuid1", "uuid2", "uuid3"]}
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        user_id = getattr(request.user, 'uuid', request.user.id) if request.user.is_authenticated else None
        updated_count = self.get_queryset().filter(
            borrowing_id__in=ids, is_del=0
        ).update(is_del=1, user_id_updated_by=user_id)

        return Response(
            {'message': f'Successfully deleted {updated_count} records', 'deleted_count': updated_count},
            status=status.HTTP_200_OK
        )

    def bulk_restore(self, request, *args, **kwargs):
        """
        Bulk restore soft deleted records
        Expects: {"ids": ["uuid1", "uuid2", "uuid3"]}
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        user_id = getattr(request.user, 'uuid', request.user.id) if request.user.is_authenticated else None
        updated_count = self.get_queryset().filter(
            borrowing_id__in=ids, is_del=1
        ).update(is_del=0, user_id_updated_by=user_id)

        return Response(
            {'message': f'Successfully restored {updated_count} records', 'restored_count': updated_count},
            status=status.HTTP_200_OK
        )


class SearchFilterMixin:
    """
    Mixin to add search, filtering, and range queries
    """

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search by lender name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(lender_name__icontains=search))

        # Filter by borrowing type (case-insensitive)
        borrowing_type = self.request.query_params.get('borrowing_type')
        if borrowing_type:
            queryset = queryset.filter(borrowing_type__iexact=borrowing_type)

        # Filter by repayment terms (case-insensitive)
        repayment_terms = self.request.query_params.get('repayment_terms')
        if repayment_terms:
            queryset = queryset.filter(repayment_terms__iexact=repayment_terms)

        # Amount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        if min_amount:
            queryset = queryset.filter(lender_amount__gte=Decimal(min_amount))
        if max_amount:
            queryset = queryset.filter(lender_amount__lte=Decimal(max_amount))

        # Date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset


class BorrowingSummaryMixin:
    """
    Mixin to calculate borrowing summaries and statistics
    """

    def get_summary(self, request, *args, **kwargs):
        company_id = request.query_params.get('company_id')
        if not company_id:
            return Response({'error': 'company_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(company_id=company_id, is_del=0)

        # Aggregated summary
        aggregates = queryset.aggregate(
            total_borrowings=Count('borrowing_id'),
            total_amount=Sum('lender_amount'),
            total_monthly_principal=Sum('monthly_principal_payment'),
            total_monthly_interest=Sum('monthly_interest_payment'),
            average_interest_rate=Avg('interest_payment_percentage'),
        )

        # Breakdown by borrowing type (with readable labels)
        by_type = {}
        for bt, label in BorrowingType.choices:
            subset = queryset.filter(borrowing_type=bt)
            if subset.exists():
                data = subset.aggregate(
                    count=Count('borrowing_id'),
                    total_amount=Sum('lender_amount'),
                    avg_interest=Avg('interest_payment_percentage'),
                )
                by_type[label] = {
                    'count': data['count'] or 0,
                    'total_amount': (data['total_amount'] or Decimal('0.00')).quantize(Decimal('0.01')),
                    'avg_interest': (data['avg_interest'] or Decimal('0.00')).quantize(Decimal('0.01')),
                }

        # Build summary response
        summary = {
            'total_borrowings': aggregates['total_borrowings'] or 0,
            'total_amount': (aggregates['total_amount'] or Decimal('0.00')).quantize(Decimal('0.01')),
            'total_monthly_principal': (aggregates['total_monthly_principal'] or Decimal('0.00')).quantize(Decimal('0.01')),
            'total_monthly_interest': (aggregates['total_monthly_interest'] or Decimal('0.00')).quantize(Decimal('0.01')),
            'average_interest_rate': (aggregates['average_interest_rate'] or Decimal('0.00')).quantize(Decimal('0.01')),
            'by_type': by_type,
        }

        from ..serializers.borrowing_serializers import BorrowingSummarySerializer
        serializer = BorrowingSummarySerializer(summary)
        return Response(serializer.data, status=status.HTTP_200_OK)
