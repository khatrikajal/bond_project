from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated 
from .models import FundPosition, CreditRating, BorrowingDetail, CapitalDetail, ProfitabilityRatio
from .serializers import (
    FundPositionSerializer,
    CreditRatingSerializer,
    BorrowingDetailSerializer,
    CapitalDetailSerializer,
    ProfitabilityRatioSerializer,
)


# Base ViewSet for Soft Delete
class BaseSoftDeleteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_del = 1
        instance.save()
        return Response({"detail": "Record soft deleted"}, status=status.HTTP_204_NO_CONTENT)


class FundPositionViewSet(BaseSoftDeleteViewSet):
    queryset = FundPosition.objects.filter(is_del=0)
    serializer_class = FundPositionSerializer


class CreditRatingViewSet(BaseSoftDeleteViewSet):
    queryset = CreditRating.objects.filter(is_del=0)
    serializer_class = CreditRatingSerializer


class BorrowingDetailViewSet(BaseSoftDeleteViewSet):
    queryset = BorrowingDetail.objects.filter(is_del=0)
    serializer_class = BorrowingDetailSerializer


class CapitalDetailViewSet(BaseSoftDeleteViewSet):
    queryset = CapitalDetail.objects.filter(is_del=0)
    serializer_class = CapitalDetailSerializer


class ProfitabilityRatioViewSet(BaseSoftDeleteViewSet):
    queryset = ProfitabilityRatio.objects.filter(is_del=0)
    serializer_class = ProfitabilityRatioSerializer
