from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from config.common.response import APIResponse
from ..models.TempUploadedFileModel import TempUploadedFile
from django.utils import timezone
import uuid
from datetime import timedelta


class TempFileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return APIResponse.error("file is required", status_code=400)

        # Save file to temp folder
        file_url, file_path = self._save_temp_file(file)

        try:
            temp = TempUploadedFile.objects.create(
                user=request.user,
                file_path=file_path,
                original_name=file.name,
                expires_at=timezone.now() + timedelta(hours=6)
            )

        except Exception as e:
            # If DB insert fails, delete physical file
            if os.path.exists(file_path):
                os.remove(file_path)

            raise e  # Will be caught by DRF exception handlers

        # Success response
        return APIResponse.success(
            message="Temp file uploaded",
            data={
                "temp_file_url": file_url,
                "original_name": file.name,
                "expires_at": temp.expires_at,
            }
        )


    def _save_temp_file(self, file):
        import os
        from django.conf import settings
        
        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)

        filename = f"{uuid.uuid4()}_{file.name}"
        full_path = os.path.join(temp_dir, filename)

        with open(full_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        # Local URL for frontend to use
        file_url = settings.MEDIA_URL + "temp_uploads/" + filename

        return file_url, full_path
