
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from datetime import datetime, timedelta


class UserManager(BaseUserManager):
    def create_user(self, email, mobile_number, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not mobile_number:
            raise ValueError("Mobile number is required")

        email = self.normalize_email(email)
        user = self.model(email=email, mobile_number=mobile_number, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, mobile_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.BigAutoField(primary_key=True, unique=True)

    # Credentials
    email = models.EmailField(blank=True, null=True, unique=False)


    password = models.CharField(max_length=128, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, unique=True)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    password_salt = models.CharField(max_length=255, null=True, blank=True)

    # KYC details
    kyc_id = models.CharField(max_length=50, null=True, blank=True)
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
        ],
        default='PENDING'
    )

    credentials_generated = models.BooleanField(default=False)
    credentials_sent_at = models.DateTimeField(null=True, blank=True)

    # Account status
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # Device tracking
    device_fingerprint = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Deletion + audit
    is_del = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user_id_updated_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_users',
    )

    objects = UserManager()

    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = ['email']


    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.email} ({self.user_id})"


class Otp(models.Model):
    OTP_TYPE_CHOICES = [
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
    ]

    otp_id = models.BigAutoField(primary_key=True, unique=True)

    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='otps'
    )

    otp_code = models.CharField(max_length=6, null=False)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES, null=False)
    expiry_time = models.DateTimeField(null=False)
    is_used = models.BooleanField(default=False)
    is_del = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    user_id_updated_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_otps'
    )

    class Meta:
        db_table = 'otp'
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        indexes = [
            models.Index(fields=['user', 'otp_type', 'is_used']),
        ]

    def __str__(self):
        return f"{self.otp_type} OTP for {self.user.email or self.user.mobile_number}"

    def is_expired(self):
        return timezone.now() > self.expiry_time

    @classmethod
    def create_static_otp(cls, user, otp_type='SMS'):
        return cls.objects.create(
            user=user,
            otp_code='1111',
            otp_type=otp_type,
            expiry_time=timezone.now() + timedelta(minutes=5)
        )
