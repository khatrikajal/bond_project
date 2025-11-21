from rest_framework import viewsets
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from apps.bond_estimate.models.CapitalDetailsModel import CapitalDetails
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication
from apps.bond_estimate.serializers.CapitalDetailsSerializer import CapitalDetailsSerializer
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
import logging
from config.common.response import APIResponse
from apps.bond_estimate.mixins.ApplicationScopedMixin import ApplicationScopedMixin
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)





class CapitalDetailsViewSet(ApplicationScopedMixin, viewsets.ModelViewSet):
    serializer_class = CapitalDetailsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "capital_detail_id"

    def get_queryset(self):
        return CapitalDetails.objects.for_application(
            self.application.application_id
        )

    # # ------------------------------------------
    # # CREATE
    # # ------------------------------------------
    # @transaction.atomic
    # def create(self, request, application_id, *args, **kwargs):

    #     application = self.application  # From mixin

    #     # Check if CapitalDetails already exists (one-to-one)
    #     existing = CapitalDetails.objects.filter(application=application).first()

    #     if existing:
    #         # Update instead of creating
    #         serializer = self.serializer_class(
    #             existing,
    #             data=request.data,
    #             partial=True
    #         )
    #         serializer.is_valid(raise_exception=True)
    #         updated = serializer.save(user_id_updated_by=request.user)

    #         self.application.mark_step(
    #             "3.2",
    #             completed=True,
    #             record_ids=[instance.pk]
    #         )


    #         return APIResponse.success(
    #             message="Capital details updated successfully",
    #             data=serializer.data,
    #             status_code=200
    #         )

    #     # Create new
    #     serializer = self.serializer_class(data=request.data)
    #     serializer.is_valid(raise_exception=True)

    #     instance = serializer.save(
    #         application=application,
    #         user_id_updated_by=request.user
    #     )

    #     self.application.mark_step(
    #             "3.2",
    #             completed=True,
    #             record_ids=[instance.pk]
    #         )

    #     return APIResponse.success(
    #         message="Capital details created successfully",
    #         data=serializer.data,
    #         status_code=201
    #     )

    # # ------------------------------------------
    # # UPDATE
    # # ------------------------------------------
    # @transaction.atomic
    # def update(self, request, application_id, *args, **kwargs):
    #     instance = self.get_object()

    #     serializer = self.serializer_class(
    #         instance,
    #         data=request.data,
    #         partial=False
    #     )
    #     serializer.is_valid(raise_exception=True)

    #     updated = serializer.save(user_id_updated_by=request.user)

    #     self.application.mark_step(
    #             "3.2",
    #             completed=True,
    #             record_ids=[updated.pk]
    #         )

    #     return APIResponse.success(
    #         message="Capital details updated successfully",
    #         data=serializer.data,
    #         status_code=200
    #     )

    # # ------------------------------------------
    # # PATCH
    # # ------------------------------------------
    # @transaction.atomic
    # def partial_update(self, request, application_id, *args, **kwargs):
    #     instance = self.get_object()

    #     serializer = self.serializer_class(
    #         instance,
    #         data=request.data,
    #         partial=True
    #     )
    #     serializer.is_valid(raise_exception=True)

    #     updated = serializer.save(user_id_updated_by=request.user)

    #     self.application.mark_step(
    #             "3.2",
    #             completed=True,
    #             record_ids=[updated.pk]
    #         )

    #     return APIResponse.success(
    #         message="Capital details updated successfully",
    #         data=serializer.data,
    #         status_code=200
    #     )

    # # ------------------------------------------
    # # DELETE
    # # ------------------------------------------
    # @transaction.atomic
    # def destroy(self, request, application_id, *args, **kwargs):
    #     instance = self.get_object()
    #     instance.del_flag = 1
    #     instance.user_id_updated_by = request.user
    #     instance.save()

    #     remaining = CapitalDetails.objects.active().filter(
    #         application=self.application
    #     ).values_list("capital_detail_id", flat=True)
        
    #     self.application.mark_step(
    #             "3.2",
    #             bool(remaining), 
    #             list(remaining)
    #         )
       

    #     return APIResponse.success(
    #         message="Capital detail deleted successfully",
    #         data={"deleted_id": instance.pk},
    #         status_code=200
    #     )

    # # ------------------------------------------
    # # LIST
    # # ------------------------------------------
    # def list(self, request, application_id, *args, **kwargs):
    #     instance = CapitalDetails.objects.filter(application=self.application, del_flag=0).first()

    #     if not instance:
    #         return APIResponse.success(
    #             message="No capital details found",
    #             data=None
    #         )

    #     serializer = self.serializer_class(instance)

    #     return APIResponse.success(
    #         message="Capital detail fetched successfully",
    #         data=serializer.data
    #     )

    # # ------------------------------------------
    # # RETRIEVE
    # # ------------------------------------------
    # def retrieve(self, request, application_id, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.serializer_class(instance)

    #     return APIResponse.success(
    #         message="Capital detail fetched successfully",
    #         data=serializer.data
    #     )




class CapitalDetailsAPI(ApplicationScopedMixin, APIView):
    """
    A SINGLE resource endpoint for CapitalDetails.
    Not a collection! (One-to-one per Application)
    """
    permission_classes = [IsAuthenticated]

    def get_instance(self):
        return CapitalDetails.objects.filter(
            application=self.application,
            del_flag=0
        ).first()

    # ---------------------------------------
    # GET (Retrieve Singleton)
    # ---------------------------------------
    def get(self, request, application_id):
        instance = self.get_instance()

        if not instance:
            return APIResponse.success(
                message="Capital details not created yet",
                data=None
            )

        serializer = CapitalDetailsSerializer(instance)
        return APIResponse.success(
            message="Capital details fetched successfully",
            data=serializer.data
        )

    # ---------------------------------------
    # POST (Create or Update Idempotently)
    # ---------------------------------------
    @transaction.atomic
    def post(self, request, application_id):
        instance = self.get_instance()

        if instance:
            # Update existing
            serializer = CapitalDetailsSerializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated = serializer.save(user_id_updated_by=request.user)

            self.application.mark_step(
                "3.2",
                completed=True,
                record_ids=[updated.pk]
            )

            return APIResponse.success(
                message="Capital details updated successfully",
                data=serializer.data
            )

        # Create new
        serializer = CapitalDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created = serializer.save(
            application=self.application,
            user_id_updated_by=request.user
        )

        self.application.mark_step(
            "3.2",
            completed=True,
            record_ids=[created.pk]
        )

        return APIResponse.success(
            message="Capital details created successfully",
            data=serializer.data,
            status_code=201
        )

    # ---------------------------------------
    # PATCH (Partial update)
    # ---------------------------------------
    @transaction.atomic
    def patch(self, request, application_id):
        instance = self.get_instance()
        if not instance:
            raise PermissionDenied("Capital details not created yet")

        serializer = CapitalDetailsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = serializer.save(user_id_updated_by=request.user)

        self.application.mark_step(
            "3.2",
            completed=True,
            record_ids=[updated.pk]
        )

        return APIResponse.success(
            message="Capital details updated successfully",
            data=serializer.data
        )

    # ---------------------------------------
    # DELETE (Soft Delete)
    # ---------------------------------------
    @transaction.atomic
    def delete(self, request, application_id):
        instance = self.get_instance()
        if not instance:
            return APIResponse.error("No capital details exist to delete")

        instance.del_flag = 1
        instance.user_id_updated_by = request.user
        instance.save()

        self.application.mark_step(
            "3.2",
            completed=False,
            record_ids=[]
        )

        return APIResponse.success(
            message="Capital details deleted successfully",
            data={"deleted_id": instance.pk}
        )