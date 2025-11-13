from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters
from django.shortcuts import get_object_or_404
from .models import ISINBasicInfo,ISINRating,FinancialMetricValue,RatioValue,ISINCompanyMap,ISINRTAMap,SnapshotDefinition
from .serializers import(ISINBasicInfoSerializer,RatioAnalysisSerializer,FinancialMetricSerializer,KeyFactorSerializer,
 ISINCompanyMapSerializer,ISINRTAMapSerializer,ISINRTAMapSerializer,ContactMessageSerializer,SnapshotItemSerializer)
from django.db.models import F, ExpressionWrapper, FloatField, Func, Subquery, OuterRef
from django.db.models.functions import  Now, Extract
from datetime import date
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
# from silk.profiling.profiler import silk_profile
from django_filters.rest_framework import DjangoFilterBackend
from .filters import BondFilter
from django.core.cache import cache
from rest_framework import status
from .services.bond_elastic_service import BondElasticService
from decimal import Decimal
from .utils import RATING_DESCRIPTIONS
from rest_framework.permissions import AllowAny
from apps.utils.swagger_base import SwaggerParamAPIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema 


from django.db.models import Case, When, Value, IntegerField, F, FloatField, Subquery, OuterRef, ExpressionWrapper, Prefetch
from django.db.models.functions import Now, Extract
from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from django_filters.rest_framework import DjangoFilterBackend

from .models import ISINBasicInfo, ISINRating
from .serializers import ISINBasicInfoSerializer
from .filters import BondFilter
from .pagination import BondCursorPagination,BondPageNumberPagination
from django.db.models import Q

# Create your views here.

class StatsView(SwaggerParamAPIView):
    permission_classes = [AllowAny]
    def get(self, request):
        data = {
            "totalIssuers": ISINBasicInfo.objects.values('issuer_name').distinct().count(),
            "totalCustomers": "1000",
            "totalBonds": ISINBasicInfo.objects.count(),
            "totalBonds": 10000,
            "stableReturnPercent": 50
        }
        return Response(data)

class BondSearchORMListView(SwaggerParamAPIView, generics.ListAPIView):
    """
    Search bonds by ISIN or issuer name using pure ORM.
    """
    permission_classes = [AllowAny]
    swagger_parameters = [
        OpenApiParameter("isin", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter bonds by ISIN code"),
        OpenApiParameter("issuerName", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter bonds by issuer name")
    ]

    serializer_class = ISINBasicInfoSerializer
    pagination_class = BondPageNumberPagination

    def get_queryset(self):
        isin = self.request.query_params.get('isin')
        issuer_name = self.request.query_params.get('issuerName')
        query = self.request.query_params.get("query")

        # Prefetch ratings
        ratings_prefetch = Prefetch(
            "ratings",
            queryset=ISINRating.objects.order_by("rating_agency", "-rating_date"),
            to_attr="latest_ratings"
        )

        # ✅ FIX: Add both tenure_days and tenure_years
        queryset = ISINBasicInfo.objects.annotate(
            tenure_days=ExpressionWrapper(
                Extract(F('maturity_date') - Now(), 'epoch') / (24 * 60 * 60),
                output_field=FloatField()
            ),
            tenure_years=ExpressionWrapper(  # ✅ Added this to match BondsListView
                Extract(F('maturity_date') - Now(), 'epoch') / (365.25 * 24 * 60 * 60),
                output_field=FloatField()
            ),
            latest_rating=Subquery(
                ISINRating.objects.filter(isin=OuterRef('pk'))
                .order_by('-rating_date')
                .values('credit_rating')[:1]
            ),
            latest_agency=Subquery(
                ISINRating.objects.filter(isin=OuterRef('pk'))
                .order_by('-rating_date')
                .values('rating_agency')[:1]
            ),
            priority=Value(1, output_field=IntegerField()),
        ).prefetch_related(ratings_prefetch).filter(isin_active=True)

        # ✅ REMOVE ALREADY MATURED BONDS
        queryset = queryset.filter(maturity_date__gte=Now())

        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(isin_code__icontains=query) |
                Q(issuer_name__icontains=query)
            )
        if isin:
            queryset = queryset.filter(isin_code__icontains=isin)
        if issuer_name:
            queryset = queryset.filter(issuer_name__icontains=issuer_name)

        # ✅ Ensure ordering consistency with BondsListView
        queryset = queryset.order_by('priority', 'tenure_days', 'tenure_years', 'isin_code')

        return queryset


class HomePageFeaturedBonds(SwaggerParamAPIView):
    """
        Returns a list of featured bonds for the homepage.
        Bonds are sorted by issue_date descending.
        Supports a 'limit' query param to specify number of bonds (default 5, max 100).
        Caches results for 5 minutes.
    """
    permission_classes = [AllowAny]
    swagger_parameters = [
    OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Number of featured bonds to return (default: 5, max: 100)")
   ]

    def get(self, request):
        limit_param = request.GET.get("limit", 5)
        try:
            limit = int(limit_param) if int(limit_param) > 0 else 5
        except (ValueError, TypeError):
            limit = 5 

        cache_key = f"home_featured_bonds_{limit}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # Subquery to get latest rating (credit_rating + agency) for each bond
        latest_rating_qs = ISINRating.objects.filter(
            isin=OuterRef("pk")
        ).order_by("-rating_date")

        featured_bonds = (
            ISINBasicInfo.objects.annotate(
                latest_rating=Subquery(latest_rating_qs.values("credit_rating")[:1]),
                latest_agency=Subquery(latest_rating_qs.values("rating_agency")[:1]),
            )
            .filter(maturity_date__gte=Now())
            .order_by("-issue_date")[:min(limit, 100)]
        
            
        )
        serializer = ISINBasicInfoSerializer(featured_bonds, many=True)
        cache.set(cache_key, serializer.data, 60 * 5)  # cache 5 min
        return Response(serializer.data)


class ExtractEpoch(Func):
    function = 'EXTRACT'
    template = "EXTRACT(EPOCH FROM %(expressions)s)"



class BondsListView(generics.ListAPIView):
    """
    API endpoint that returns a list of bonds.
    Prioritizes ISIN or Issuer Name if provided in query params.
    """
    permission_classes = [AllowAny]
    serializer_class = ISINBasicInfoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = BondFilter
    ordering_fields = ['priority', 'tenure_days', 'tenure_years', 'ytm_percent']
    pagination_class = BondPageNumberPagination

    swagger_parameters = [
        OpenApiParameter("isin", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Prioritize by ISIN"),
        OpenApiParameter("issuer_name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Prioritize by Issuer Name"),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Sort by 'priority', 'tenure_days', 'tenure_years' or 'ytm_percent'"),
    ]

    def get_queryset(self):
        ratings_prefetch = Prefetch(
            "ratings",
            queryset=ISINRating.objects.order_by("rating_agency", "-rating_date"),
            to_attr="latest_ratings"
        )

        # Base queryset with default annotations
        queryset = (
            ISINBasicInfo.objects.annotate(
                tenure_days=ExpressionWrapper(
                    Extract('maturity_date', 'epoch') - Extract(Now(), 'epoch'),
                    output_field=FloatField()
                ) / (24 * 60 * 60),

                tenure_years=ExpressionWrapper(
                    ExtractEpoch(F('maturity_date') - Now()) / (365.25 * 24 * 60 * 60),
                    output_field=FloatField()
                ),

                latest_rating=Subquery(
                    ISINRating.objects.filter(isin=OuterRef('pk'))
                    .order_by('-rating_date')
                    .values('credit_rating')[:1]
                ),
                latest_agency=Subquery(
                    ISINRating.objects.filter(isin=OuterRef('pk'))
                    .order_by('-rating_date')
                    .values('rating_agency')[:1]
                ),
                priority=Value(1, output_field=IntegerField()),  # default priority
            )
            .prefetch_related(ratings_prefetch)
            .filter(isin_active=True)
        )

        # ✅ REMOVE ALREADY MATURED BONDS
        queryset = queryset.filter(maturity_date__gte=Now())

        isin = self.request.query_params.get('isin')
        issuer_name = self.request.query_params.get('issuer_name')

        # ✅ Prioritize ISIN
        if isin:
            queryset = queryset.annotate(
                priority=Case(
                    When(isin_code__iexact=isin, then=Value(0)),
                    default=F('priority'),
                    output_field=IntegerField()
                )
            )

        # ✅ Prioritize Issuer Name if ISIN not given
        elif issuer_name:
            queryset = queryset.annotate(
                priority=Case(
                    When(issuer_name__icontains=issuer_name, then=Value(0)),
                    default=F('priority'),
                    output_field=IntegerField()
                )
            )

        # ✅ Order by priority first, then other fields
        queryset = queryset.order_by('priority', 'tenure_days', 'tenure_years', 'ytm_percent', 'isin_code')

        # ✅ Ensure pagination respects ordering
        self.pagination_class.ordering = ['priority', 'tenure_days', 'tenure_years', 'ytm_percent', 'isin_code']

        return queryset


class BondDetailView(SwaggerParamAPIView):
    """
    Retrieve detailed information about a specific bond by ISIN code."""
    permission_classes = [AllowAny]
    swagger_parameters = [
    OpenApiParameter("isin", OpenApiTypes.STR, OpenApiParameter.QUERY, description="ISIN code of the bond to fetch details")
    ]

    def get(self, request):
        isin_code = request.GET.get("isin")
        bond = get_object_or_404(
            ISINBasicInfo.objects.prefetch_related(
                Prefetch(
                    "company_mappings",
                    queryset=ISINCompanyMap.objects.select_related("company").filter(primary_company=True),
                    to_attr="primary_companies"
                ),
                Prefetch(
                    "rta_mappings",
                    queryset=ISINRTAMap.objects.select_related("rta"),
                    to_attr="rta_list"
                ),
                Prefetch(
                    "ratings",
                    queryset=ISINRating.objects.order_by("rating_agency", "-rating_date"),
                    to_attr="latest_ratings"
                )
            ),
            isin_code=isin_code
        )

        company_map = bond.primary_companies[0] if bond.primary_companies else None
        rta_map = bond.rta_list[0] if bond.rta_list else None

        company_data = ISINCompanyMapSerializer(company_map).data if company_map and company_map.company else None
        rta_data = ISINRTAMapSerializer(rta_map).data if rta_map and rta_map.rta else None

        data = {
            "bond": ISINBasicInfoSerializer(bond).data,
            "company": company_data,
            # "rta": rta_data,
        }

        # <-- You MUST return a Response here
        return Response(data, status=status.HTTP_200_OK)



class SimilarBondsView(SwaggerParamAPIView):
    """
    Returns bonds similar to a given ISIN based on:
    - Latest credit rating
    - YTM (±0.5% tolerance by default)
    Supports optional 'limit' query parameter.
    """
    permission_classes = [AllowAny]
    swagger_parameters = [
    OpenApiParameter("isin", OpenApiTypes.STR, OpenApiParameter.QUERY, description="ISIN code to find similar bonds"),
    OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Maximum number of results (default: 50)")
    ]

    def get(self, request):
        isin_code = request.query_params.get("isin")
        limit = request.query_params.get("limit", 50)  # default limit
        try:
            limit = int(limit)
        except ValueError:
            return Response({"error": "Limit must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        if not isin_code:
            return Response({"error": "ISIN is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bond = ISINBasicInfo.objects.get(isin_code=isin_code, isin_active=True)
        except ISINBasicInfo.DoesNotExist:
            return Response({"error": "Bond not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get latest rating for base bond
        latest_rating = ISINRating.objects.filter(isin=bond).order_by('-rating_date').first()
        rating_value = latest_rating.credit_rating if latest_rating else None

        # YTM tolerance
        ytm_tolerance = Decimal("0.5")  # Convert tolerance to Decimal
        ytm_min = (bond.ytm_percent or Decimal("0")) - ytm_tolerance
        ytm_max = (bond.ytm_percent or Decimal("0")) + ytm_tolerance

        # Annotate latest rating to avoid join duplication
        latest_rating_subquery = Subquery(
            ISINRating.objects.filter(isin=OuterRef('pk')).order_by('-rating_date').values('credit_rating')[:1]
        )

        similar_bonds_qs = ISINBasicInfo.objects.annotate(
            latest_rating=latest_rating_subquery
        ).filter(
            isin_active=True,
            ytm_percent__gte=ytm_min,
            ytm_percent__lte=ytm_max
        ).exclude(isin_code=isin_code)
        similar_bonds_qs = similar_bonds_qs.filter(tenure_days__gte=0)
        
        if rating_value:
            similar_bonds_qs = similar_bonds_qs.filter(maturity_date__gte=Now())
        
        # Prefetch ratings for serializer
        similar_bonds_qs = similar_bonds_qs.prefetch_related(
            Prefetch(
                "ratings",
                queryset=ISINRating.objects.order_by("-rating_date"),
                to_attr="latest_ratings"
            )
        )[:limit]
        
        serializer = ISINBasicInfoSerializer(similar_bonds_qs, many=True)
        return Response(serializer.data)


class BondResearchDataView(SwaggerParamAPIView):
    """  
    Retrieve research data (financial metrics, ratio analysis, key factors) for the company associated with a given bond ISIN.
    """
    permission_classes = [AllowAny]
    swagger_parameters = [
    OpenApiParameter("isin", OpenApiTypes.STR, OpenApiParameter.QUERY, description="ISIN code of the bond to fetch research data")
]

    def get(self, request):
        isin_code = request.GET.get("isin")
        bond = get_object_or_404(ISINBasicInfo, isin_code=isin_code)

        # Step 1: Get the company mapped to this ISIN
        company = (
            bond.company_mappings.filter(primary_company=True)
            .select_related("company")
            .prefetch_related(
                Prefetch(
                    "company__financial_metrics__values",
                    queryset=FinancialMetricValue.objects.order_by("-year"),
                ),
                Prefetch(
                    "company__ratio_analyses__values",
                    queryset=RatioValue.objects.order_by("-year"),
                ),
                # "company__key_factors"
            )
            .first()
        )

        if not company:
            return Response(
                {"error": "No company mapping found for this ISIN"},
                status=status.HTTP_404_NOT_FOUND,
            )

        company = company.company  # actual CompanyInfo instance

        # Step 2: Serialize related company data
        data = {
            "financialMetrics": FinancialMetricSerializer(
                company.financial_metrics.all(), many=True
            ).data,
            "ratioAnalysis": RatioAnalysisSerializer(
                company.ratio_analyses.all(), many=True
            ).data,
            # "keyFactors": KeyFactorSerializer(
            #     company.key_factors, many=False
            # ).data if hasattr(company, "key_factors") else None,
        }

        return Response(data, status=status.HTTP_200_OK)


class BondSnapshotView(SwaggerParamAPIView):
    """
    Returns a UI-ready Key Financial & Rating Snapshot for a given bond ISIN.
    Only includes financial metrics and credit ratings.
    """
    permission_classes = [AllowAny]
    swagger_parameters = [
    OpenApiParameter("isin", OpenApiTypes.STR, OpenApiParameter.QUERY, description="ISIN code of the bond for snapshot")
]

    def get(self, request):
        isin_code = request.GET.get("isin")
        if not isin_code:
            return Response({"error": "ISIN code required"}, status=status.HTTP_400_BAD_REQUEST)

        bond = get_object_or_404(
            ISINBasicInfo.objects.prefetch_related(
                Prefetch(
                    "ratings",
                    queryset=ISINRating.objects.order_by('rating_agency', '-rating_date'),
                    to_attr="all_ratings"
                ),
                Prefetch(
                    "company_mappings__company__financial_metrics__values",
                    queryset=FinancialMetricValue.objects.order_by("-year"),
                ),
                "company_mappings__company"
            ),
            isin_code=isin_code
        )

        company_mapping = next((cm for cm in bond.company_mappings.all() if cm.primary_company), None)
        if not company_mapping:
            return Response({"error": "No primary company mapping found for this ISIN"}, status=404)

        company = company_mapping.company
        snapshot = []

        # ---- Credit Ratings ----
        latest_ratings = {}
        for rating in bond.all_ratings:
            if rating.rating_agency not in latest_ratings:
                latest_ratings[rating.rating_agency] = rating.credit_rating

        rating_str = "; ".join(
            [f"[{agency}] {rating} ({RATING_DESCRIPTIONS.get(rating, '')})"
             for agency, rating in latest_ratings.items()]
        )
        snapshot.append({"metric": "Credit Rating / Outlook", "value": rating_str})

        # ---- Financial Metrics from SnapshotDefinition ----
        snapshot_defs = SnapshotDefinition.objects.filter(metric_type='financial').order_by('order')
        for sd in snapshot_defs:
            metric = next((m for m in company.financial_metrics.all() if m.name == sd.metric_name), None)
            if metric and metric.values.exists():
                latest_value = max(metric.values.all(), key=lambda v: v.year)
                value_str = f"~ ₹ {latest_value.value} Crore (as of {latest_value.year})"
                snapshot.append({"metric": sd.display_name, "value": value_str})

        serializer = SnapshotItemSerializer(snapshot, many=True)
        return Response({"company": company.issuer_name, "snapshot": serializer.data}, status=status.HTTP_200_OK)


class ContactMessageView(SwaggerParamAPIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ContactMessageSerializer,
        responses={201: dict, 400: dict},
        description="Submit a contact message with name, email, phone number, and message."
    )
    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Your message has been added successfully!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)