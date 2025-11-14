from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication
from apps.bond_estimate.models.ProfitabilityRatiosModel  import ProfitabilityRatios
from apps.bond_estimate.serializers.ProfitabilityRatiosSerializer import ProfitabilityRatiosSerializer
from config.common.response import APIResponse


class ProfitabilityRatiosViewSet(viewsets.ModelViewSet):
    serializer_class = ProfitabilityRatiosSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "ratio_id"
    lookup_url_kwarg = "ratio_id"

    # ---------------------------------------------------
    # OPTIMIZED QUERYSET  (select_related)
    # ---------------------------------------------------
    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        return (
            ProfitabilityRatios.objects
            .select_related("company")           
            .filter(company_id=company_id, del_flag=0)
        )

    # ---------------------------------------------------
    # HELPER — CHECK IF ALL REQUIRED RATIOS ARE FILLED
    # ---------------------------------------------------
    def _all_required_ratios_filled(self, instance):
        required_fields = [
            "net_profit",
            "net_worth",
            "ebitda",
            "debt_equity_ratio",
            "current_ratio",
            "quick_ratio",
            "return_on_equity",
            "return_on_assets",
            "dscr",
        ]
        return all(getattr(instance, field) is not None for field in required_fields)

    # ---------------------------------------------------
    # HELPER — UPDATE STEP STATUS
    # ---------------------------------------------------
    def _update_ratios_step_status(self, company_id, instance=None):
        """
        Optimized: uses the already-saved instance if passed.
        """
        try:
            app = BondEstimationApplication.objects.get(company_id=company_id)
        except BondEstimationApplication.DoesNotExist:
            return

        # Use passed instance instead of querying again
        if instance is None:
            instance = (
                ProfitabilityRatios.objects
                .filter(company_id=company_id, del_flag=0)
                .only("ratio_id")       
                .first()
            )

        if not instance:
            app.mark_step("2.2", completed=False, record_ids=[])
            return

        is_complete = self._all_required_ratios_filled(instance)

        app.mark_step(
            "2.2",
            completed=is_complete,
            record_ids=[instance.pk] if is_complete else [],
        )

    # ---------------------------------------------------
    # CREATE (idempotent)
    # ---------------------------------------------------
    @transaction.atomic
    def create(self, request, company_id, *args, **kwargs):

        queryset = self.get_queryset()   
        existing = queryset.first()

        if existing:
            # update instead of creating new
            serializer = self.serializer_class(
                existing, data=request.data, partial=True, context={"view": self, "request": request}
            )
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user_id_updated_by=request.user)

            # use saved instance for step check (no extra DB)
            self._update_ratios_step_status(company_id, instance)

            return APIResponse.success(
                message="Profitability ratios updated successfully (idempotent)",
                data=serializer.data,
                status_code=200
            )

        # create new
        serializer = self.serializer_class(data=request.data, context={"view": self, "request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user_id_updated_by=request.user)

        self._update_ratios_step_status(company_id, instance)

        return APIResponse.success(
            message="Profitability ratios created successfully",
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
            instance, data=request.data, partial=False, context={"view": self, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user_id_updated_by=request.user)

        self._update_ratios_step_status(company_id, instance)

        return APIResponse.success(
            message="Profitability ratios updated successfully",
            data=serializer.data,
            status_code=200
        )

    # ---------------------------------------------------
    # PATCH (PARTIAL UPDATE)
    # ---------------------------------------------------
    @transaction.atomic
    def partial_update(self, request, company_id, *args, **kwargs):
        instance = self.get_object()

        serializer = self.serializer_class(
            instance, data=request.data, partial=True, context={"view": self, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user_id_updated_by=request.user)

        self._update_ratios_step_status(company_id, instance)

        return APIResponse.success(
            message="Profitability ratios updated successfully",
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

        self._update_ratios_step_status(company_id, instance=None)

        return APIResponse.success(
            message="Profitability ratios deleted successfully",
            data={"deleted_id": instance.pk},
            status_code=200
        )

    # ---------------------------------------------------
    # LIST
    # ---------------------------------------------------
    def list(self, request, company_id, *args, **kwargs):
        queryset = self.get_queryset()  
        serializer = self.serializer_class(queryset, many=True, context={"view": self, "request": request})

        return APIResponse.success(
            message="Profitability ratios fetched successfully",
            data=serializer.data,
            status_code=200
        )

    # ---------------------------------------------------
    # RETRIEVE
    # ---------------------------------------------------
    def retrieve(self, request, company_id, *args, **kwargs):
        instance = self.get_object() 
        serializer = self.serializer_class(instance, context={"view": self, "request": request})

        return APIResponse.success(
            message="Profitability ratio fetched successfully",
            data=serializer.data,
            status_code=200
        )
