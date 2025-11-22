from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from config.common.response import APIResponse
from apps.bond_estimate.models.borrowing_details import BorrowingType, RepaymentTerms

class BorrowingChoicesAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        borrowing_types = [{"value": v, "label": l} for v, l in BorrowingType.choices]
        repayment_terms = [{"value": v, "label": l} for v, l in RepaymentTerms.choices]

        return APIResponse.success(
            message="Borrowing choices fetched",
            data={
                "borrowing_types": borrowing_types,
                "repayment_terms": repayment_terms
            }
        )
