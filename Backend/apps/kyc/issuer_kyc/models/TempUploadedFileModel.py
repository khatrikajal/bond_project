from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
import uuid


class TempUploadedFile(models.Model):
    temp_file_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_path = models.TextField()     # S3 path or local path
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # now + X hours
    is_used = models.BooleanField(default=False)  # becomes True when promoted