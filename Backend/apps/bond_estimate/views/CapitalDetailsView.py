from rest_framework import viewsets
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from apps.bond_estimate.models.CapitalDetailsModel import CapitalDetails
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication
from apps.bond_estimate.serializers.CapitalDetailsSerializer import CapitalDetailsSerializer
import logging
from config.common.response import APIResponse


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)





class CapitalDetailsViewSet(viewsets.ModelViewSet):
    serializer_class = CapitalDetailsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'capital_detail_id'

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        return CapitalDetails.objects.filter(company_id=company_id, del_flag=0)

    def _mark_step(self, company_id, step_completed, record_ids=None):
        try:
            app = BondEstimationApplication.objects.get(company_id=company_id)
            app.mark_step("2.1", completed=step_completed, record_ids=record_ids)
        except BondEstimationApplication.DoesNotExist:
            pass

    # ---------------------------------------------------
    # CREATE
    # ---------------------------------------------------
    @transaction.atomic
    def create(self, request, company_id, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ 1. Check if record already exists (idempotent behavior)
        existing = CapitalDetails.objects.filter(
            company_id=company_id,
            del_flag=0
        ).first()

        if existing:
            # ✅ 2. Update instead of creating a new record
            updated_serializer = self.serializer_class(
                existing,
                data=request.data,
                partial=True
            )
            updated_serializer.is_valid(raise_exception=True)

            updated = updated_serializer.save(
                user_id_updated_by=request.user
            )

            self._mark_step(
                company_id,
                step_completed=True,
                record_ids=[updated.pk]
            )

            return APIResponse.success(
                message="Capital details updated successfully (idempotent)",
                data=updated_serializer.data,
                status_code=200
            )

        # ✅ 3. Create new record if none exists
        instance = serializer.save(
            company_id=company_id,
            user_id_updated_by=request.user,
        )

        self._mark_step(
            company_id,
            step_completed=True,
            record_ids=[instance.pk]
        )

        return APIResponse.success(
            
            message="Capital details created successfully",
            data=serializer.data,
            status_code=201
        )



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

        self._mark_step(
            company_id,
            step_completed=True,
            record_ids=[updated.pk]
        )

        return APIResponse.success(
            message="Capital details updated successfully",
            data=serializer.data,
            status_code=200
        )

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

        self._mark_step(
            company_id,
            step_completed=True,
            record_ids=[updated.pk]
        )

        return APIResponse.success(
         
            message="Capital details updated successfully",
            data=serializer.data,
            status_code=200
        )

    # ---------------------------------------------------
    # DELETE (SOFT DELETE)
    # ---------------------------------------------------
    @transaction.atomic
    def destroy(self, request, company_id, *args, **kwargs):
        instance = self.get_object()
        instance.del_flag = 1
        instance.user_id_updated_by = request.user
        instance.save()

        remaining = CapitalDetails.objects.filter(
            company_id=company_id,
            del_flag=0
        ).values_list("capital_detail_id", flat=True)

        if remaining:
            self._mark_step(
                company_id,
                step_completed=True,
                record_ids=list(remaining)
            )
        else:
            self._mark_step(
                company_id,
                step_completed=False,
                record_ids=[]
            )

        return APIResponse.success(
            message="Capital detail deleted successfully",
            data={"deleted_id": instance.pk},
            status_code=200
        )
    
       
    # ---------------------------------------------------
    # LIST (GET ALL)
    # ---------------------------------------------------
    def list(self, request, company_id, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)

        return APIResponse.success(
        message="Capital detail fetched successfully",
        data=serializer.data,
        status_code=200
        )


    # ---------------------------------------------------
    # RETRIEVE (GET ONE)
    # ---------------------------------------------------
    def retrieve(self, request, company_id, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance)

        return APIResponse.success(
            message="Capital detail fetched successfully",
            data=serializer.data,
            status_code=200
        )
        
