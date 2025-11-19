from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from ..serializers.CreditRatingSerializer import (
    CreditRatingSerializer,
    CreditRatingPutSerializer,
    CreditRatingListSerializer,
)
from ..models.CreditRatingDetailsModel import CreditRatingDetails
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from config.common.response import APIResponse
from ..services.bond_estimation_service import create_or_get_application, update_step
from ..models.AgencyRatingChoice import RatingAgency, CreditRating


# ------------------------------------------------
# CREATE CREDIT RATING (Multiple allowed)
# ------------------------------------------------
class CreditRatingCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, company_id):
        serializer = CreditRatingSerializer(
            data=request.data,
            context={"request": request, "company_id": company_id},
        )
        serializer.is_valid(raise_exception=True)
        rating_entry = serializer.save()

        company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
        app = create_or_get_application(user=request.user, company=company)

        response = CreditRatingListSerializer(rating_entry, context={'request': request}).data
        response.update({
            "application_id": str(app.application_id),
            "step_id": "1.2",
            "step_status": "completed",
        })

        return APIResponse.success(
            data=response,
            message="Credit rating saved successfully",
            status_code=201
        )


# ------------------------------------------------
# LIST CREDIT RATINGS
# ------------------------------------------------
class CreditRatingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
        ratings = CreditRatingDetails.objects.filter(company=company, is_del=0).order_by('-created_at')

        serializer = CreditRatingListSerializer(ratings, many=True, context={'request': request})

        app = create_or_get_application(user=request.user, company=company)
        step_state = app.get_step_state("1.2")

        return APIResponse.success(
            data={
                "ratings": serializer.data,
                "total_count": ratings.count(),
                "application_id": str(app.application_id),
                "step_completed": step_state.get("completed", False),
                "step_updated_at": step_state.get("updated_at"),
            },
            message="Credit ratings fetched successfully"
        )


# ------------------------------------------------
# DETAIL / UPDATE / DELETE
# ------------------------------------------------
class CreditRatingDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, company_id, credit_rating_id, user):
        company = CompanyInformation.objects.get(company_id=company_id, user=user)
        return CreditRatingDetails.objects.get(
            credit_rating_id=credit_rating_id,
            company=company,
            is_del=0
        )

    # -----------------------
    # GET BY ID
    # -----------------------
    def get(self, request, credit_rating_id, company_id):
        rating = self.get_object(company_id, credit_rating_id, request.user)
        serializer = CreditRatingListSerializer(rating, context={'request': request})
        return APIResponse.success(
            data=serializer.data,
            message="Credit rating fetched successfully"
        )

    # -----------------------
    # FULL UPDATE (PUT) – Requires all fields
    # -----------------------
    def put(self, request, credit_rating_id, company_id):
        rating = self.get_object(company_id, credit_rating_id, request.user)

        serializer = CreditRatingPutSerializer(
            data=request.data,
            context={"request": request, "company_id": company_id, "instance": rating},
        )
        serializer.is_valid(raise_exception=True)
        updated_rating = serializer.update(rating, serializer.validated_data)

        response = CreditRatingListSerializer(updated_rating, context={'request': request}).data
        return APIResponse.success(
            data=response,
            message="Credit rating fully updated successfully"
        )

    # -----------------------
    # PARTIAL UPDATE (PATCH) – Only changed fields required
    # -----------------------
    def patch(self, request, credit_rating_id, company_id):
        rating = self.get_object(company_id, credit_rating_id, request.user)

        serializer = CreditRatingSerializer(
            data=request.data,
            partial=True,
            context={"request": request, "company_id": company_id, "instance": rating},
        )
        serializer.is_valid(raise_exception=True)
        updated_rating = serializer.update(rating, serializer.validated_data)

        response = CreditRatingListSerializer(updated_rating, context={'request': request}).data
        return APIResponse.success(
            data=response,
            message="Credit rating partially updated successfully"
        )

    # -----------------------
    # DELETE
    # -----------------------
    def delete(self, request, credit_rating_id, company_id):
        rating = self.get_object(company_id, credit_rating_id, request.user)
        rating.is_del = 1
        rating.user_id_updated_by = request.user
        rating.save(update_fields=['is_del', 'user_id_updated_by', 'updated_at'])

        # Update step if no ratings left
        company = rating.company
        remaining = CreditRatingDetails.objects.filter(company=company, is_del=0).exists()

        if not remaining:
            app = create_or_get_application(user=request.user, company=company)
            update_step(app, "1.2", [], False)

        return APIResponse.success(message="Credit rating deleted successfully")


# ------------------------------------------------
# RATING & AGENCY CHOICES
# ------------------------------------------------
class CreditRatingAgencyChoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return APIResponse.success(
            data={
                "agencies": [{"value": v, "label": lbl} for v, lbl in RatingAgency.choices],
                "ratings": [{"value": v, "label": lbl} for v, lbl in CreditRating.choices],
            },
            message="Rating choices retrieved successfully"
        )


# ------------------------------------------------
# BULK DELETE CREDIT RATINGS
# ------------------------------------------------
class CreditRatingBulkDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        rating_ids = request.data.get('credit_rating_ids')

        if not rating_ids or not isinstance(rating_ids, list):
            return APIResponse.error(
                message="Invalid credit_rating_ids provided",
                errors={"credit_rating_ids": "Must be a list of IDs"},
                status_code=400
            )

        company = CompanyInformation.objects.get(company_id=company_id, user=request.user)

        deleted_count = CreditRatingDetails.objects.filter(
            credit_rating_id__in=rating_ids,
            company=company,
            is_del=0
        ).update(is_del=1, user_id_updated_by=request.user)

        # Update step if no ratings left
        if not CreditRatingDetails.objects.filter(company=company, is_del=0).exists():
            app = create_or_get_application(user=request.user, company=company)
            update_step(app, "1.2", [], False)

        return APIResponse.success(
            data={"deleted_count": deleted_count},
            message=f"{deleted_count} credit rating(s) deleted successfully"
        )
