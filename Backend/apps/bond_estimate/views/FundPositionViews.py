import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.bond_estimate.mixins.ApplicationScopedMixin import ApplicationScopedMixin
from apps.bond_estimate.models.FundPositionModel import FundPosition
from apps.bond_estimate.serializers.FundPositionSerializer import FundPositionSerializer
from config.common.response import APIResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FundPositionAPI(ApplicationScopedMixin, APIView):
    permission_classes = [IsAuthenticated]

    STEP_ID = "1.1"

    def get_instance(self):
        return FundPosition.objects.filter(
            application=self.application
        ).first()

    def _mark_step(self, record_id=None):
        if record_id:
            record_ids = [record_id]
            completed = True
        else:
            record_ids = []
            completed = False

        self.application.mark_step(
            step_id=self.STEP_ID,
            completed=completed,
            record_ids=record_ids
        )

    def get(self, request, application_id):
        instance = self.get_instance()
        if not instance or instance.del_flag == 1:
            return APIResponse.success("Fund position not created yet", None)

        serializer = FundPositionSerializer(instance)
        return APIResponse.success("Fund position fetched successfully", serializer.data)

    @transaction.atomic
    def post(self, request, application_id):
        instance = self.get_instance()

        # UPDATE / RESTORE
        if instance:
            if instance.del_flag == 1:
                instance.del_flag = 0

            serializer = FundPositionSerializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            updated = serializer.save(user_id_updated_by=request.user)

            self._mark_step(str(updated.fund_position_id))

            return APIResponse.success("Fund position updated successfully", serializer.data)

        # CREATE
        serializer = FundPositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created = serializer.save(
            application=self.application,
            user_id_updated_by=request.user
        )

        self._mark_step(str(created.fund_position_id))

        return APIResponse.success("Fund position created successfully", serializer.data, 201)

    @transaction.atomic
    def patch(self, request, application_id):
        instance = self.get_instance()
        if not instance or instance.del_flag == 1:
            return APIResponse.error("Fund position not created yet", 404)

        serializer = FundPositionSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = serializer.save(user_id_updated_by=request.user)

        self._mark_step(str(updated.fund_position_id))

        return APIResponse.success("Fund position updated successfully", serializer.data)

    @transaction.atomic
    def delete(self, request, application_id):
        instance = self.get_instance()
        if not instance or instance.del_flag == 1:
            return APIResponse.error("Fund position not found", 404)

        instance.del_flag = 1
        instance.user_id_updated_by = request.user
        instance.save()

        self._mark_step(None)

        return APIResponse.success(
            "Fund position deleted successfully",
            {"deleted_id": str(instance.fund_position_id)}
        )
