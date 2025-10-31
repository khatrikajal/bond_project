# from .model import IssureAuthActivityLog
# from django.utils import timezone
# from rest_framework.exceptions import ValidationError

# def log_activity(
#     activity_type,
#     description=None,
#     user=None,
#     severity="INFO",
#     ip_address=None,
#     device_fingerprint=None,
#     user_agent=None,
#     session_id=None,
#     metadata=None,
#     related_table=None,
#     related_record_id=None,
#     updated_by=None,
#     request=None
# ):
#     """
#     Creates a standardized log entry in IssureAuthActivityLog table.

#     This function can be called anywhere: serializers, views, or signals.
#     Automatically extracts IP, User Agent, and Session ID if request is passed.
#     """

#     # 🧠 Auto-extract info from request
#     if request:
#         # Ensure session exists for APIs (Django REST doesn't always create it)
#         if not request.session.session_key:
#             request.session.save()

#         ip_address = ip_address or get_client_ip(request)
#         user_agent = user_agent or request.META.get("HTTP_USER_AGENT", "")
#         session_id = session_id or request.session.session_key

#     # 📝 Create the log entry
#     log = IssureAuthActivityLog.objects.create(
#         user=user,
#         activity_type=activity_type,
#         description=description,
#         severity=severity,
#         ip_address=ip_address,
#         device_fingerprint=device_fingerprint,
#         user_agent=user_agent,
#         session_id=session_id,
#         metadata=metadata or {},
#         related_table=related_table,
#         related_record_id=related_record_id,
#         user_id_updated_by=updated_by,
#         created_at=timezone.now(),
#     )

#     return log


# def get_client_ip(request):
#     """
#     Safely extract client IP address even behind proxy or load balancer.
#     """
#     x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(",")[0].strip()
#     else:
#         ip = request.META.get("REMOTE_ADDR")
#     return ip or "0.0.0.0"


# def raise_validation_error(message, *, activity_type, severity="ERROR", user=None, request=None, metadata=None, related_table=None, related_record_id=None):
#     """
#     Logs the failure and raises a DRF ValidationError.
#     Keeps your serializers clean.
#     """
#     log_activity(
#         user=user,
#         activity_type=activity_type,
#         description=message,
#         severity=severity,
#         request=request,
#         metadata=metadata,
#         related_table=related_table,
#         related_record_id=related_record_id,
#     )
#     raise ValidationError(message)