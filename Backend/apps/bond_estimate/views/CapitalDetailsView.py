from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from rest_framework.permissions import IsAuthenticated

# from apps.bond_estimate.models.CapitalDetailsModel import CapitalDetails
# from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication
# from apps.bond_estimate.serializers.CapitalDetailsSerializer import CapitalDetailsSerializer

from apps.bond_estimate.models.CapitalDetailsModel import CapitalDetails
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication
from apps.bond_estimate.serializers.CapitalDetailsSerializer import CapitalDetailsSerializer


class CapitalDetailsViewSet(viewsets.ModelViewSet):
    serializer_class = CapitalDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        return CapitalDetails.objects.filter(company_id=company_id, del_flag=0)

    def _mark_step(self, company_id, step_completed, record_ids=None):
        """
        Internal helper to mark onboarding step 2.1
        """
        try:
            app = BondEstimationApplication.objects.get(company_id=company_id)
            app.mark_step(
                "2.1",
                completed=step_completed,
                record_ids=record_ids
            )
        except BondEstimationApplication.DoesNotExist:
            pass

    # ---------------------------------------------------
    # CREATE
    # ---------------------------------------------------
    @transaction.atomic
    def create(self, request, company_id, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(
            company_id=company_id,
            user_id_updated_by=request.user,
        )

        # ✅ Step 2.1 should be marked complete after successful create
        self._mark_step(
            company_id,
            step_completed=True,
            record_ids=[instance.pk]
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------
    # UPDATE (PUT)
    # ---------------------------------------------------
    @transaction.atomic
    def update(self, request, company_id, *args, **kwargs):
        instance = self.get_object()

        serializer = self.serializer_class(
            instance,
            data=request.data,
            partial=False
        )
        serializer.is_valid(raise_exception=True)

        updated = serializer.save(user_id_updated_by=request.user)

        # ✅ Step stays completed; record_ids preserved
        self._mark_step(
            company_id,
            step_completed=True,
            record_ids=[updated.pk]
        )

        return Response(serializer.data)

    # ---------------------------------------------------
    # PARTIAL UPDATE (PATCH)
    # ---------------------------------------------------
    @transaction.atomic
    def partial_update(self, request, company_id, *args, **kwargs):
        instance = self.get_object()

        serializer = self.serializer_class(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        updated = serializer.save(user_id_updated_by=request.user)

        # ✅ Step stays complete
        self._mark_step(
            company_id,
            step_completed=True,
            record_ids=[updated.pk]
        )

        return Response(serializer.data)

    # ---------------------------------------------------
    # DELETE (SOFT DELETE)
    # ---------------------------------------------------
    @transaction.atomic
    def destroy(self, request, company_id, *args, **kwargs):

        instance = self.get_object()
        instance.del_flag = 1
        instance.user_id_updated_by = request.user
        instance.save()

        # ✅ Check if ANY records remain for this company
        remaining = CapitalDetails.objects.filter(
            company_id=company_id,
            del_flag=0
        ).values_list("capital_detail_id", flat=True)

        if remaining:
            # Still completed; update record_ids list
            self._mark_step(
                company_id,
                step_completed=True,
                record_ids=list(remaining)
            )
        else:
            # No records → step not completed
            self._mark_step(
                company_id,
                step_completed=False,
                record_ids=[]
            )

        return Response(
            {"detail": "Deleted successfully"},
            status=status.HTTP_200_OK
        )
    

    def _mark_step(self, company_id, step_completed, record_ids=None):
        app = BondEstimationApplication.objects.get(company_id=company_id)
        app.mark_step("2.1", completed=step_completed, record_ids=record_ids)

