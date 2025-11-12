# apps/bond_estimate/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.borrowing_views import BorrowingDetailsViewSet  # adjust import if needed

# Initialize the DRF router
router = DefaultRouter()
router.register(r'borrowing', BorrowingDetailsViewSet, basename='borrowing')

# Define URL patterns
urlpatterns = [
    path('', include(router.urls)),

    # Example for future extension:
    # path('borrowing/export/', BorrowingExportView.as_view(), name='borrowing-export'),
]

"""
===========================================
Bond Estimate API Endpoints
===========================================

Base URL:
    /api/bond_estimate/borrowing/

Standard CRUD Endpoints:
-------------------------------------------
- GET    /api/bond_estimate/borrowing/                     → List all borrowing records
- POST   /api/bond_estimate/borrowing/                     → Create a new borrowing record
- GET    /api/bond_estimate/borrowing/{uuid}/              → Retrieve specific borrowing by UUID
- PUT    /api/bond_estimate/borrowing/{uuid}/              → Full update
- PATCH  /api/bond_estimate/borrowing/{uuid}/              → Partial update
- DELETE /api/bond_estimate/borrowing/{uuid}/              → Soft delete

Custom Actions (optional if implemented in ViewSet):
-------------------------------------------
- POST   /api/bond_estimate/borrowing/bulk_create/         → Bulk create borrowings
- POST   /api/bond_estimate/borrowing/bulk_delete/         → Bulk soft delete by UUID list
- POST   /api/bond_estimate/borrowing/bulk_restore/        → Bulk restore deleted records
- GET    /api/bond_estimate/borrowing/summary/             → Summary statistics for borrowings
- GET    /api/bond_estimate/borrowing/choices/             → Dropdown field options
- GET    /api/bond_estimate/borrowing/company_borrowings/  → Borrowings by company UUID
- POST   /api/bond_estimate/borrowing/{uuid}/restore/      → Restore a single deleted record

Query Parameters (for list endpoint):
-------------------------------------------
- company_id       → Filter by company (UUID)
- search           → Search by lender name
- borrowing_type   → Filter by borrowing type
- repayment_terms  → Filter by repayment terms
- min_amount       → Minimum lender amount
- max_amount       → Maximum lender amount
- start_date       → Filter from date
- end_date         → Filter to date
- ordering         → Sort field (e.g., -created_at, lender_amount)
- page             → Page number
- page_size        → Items per page
- include_deleted  → Include soft-deleted records (true/false)
"""
