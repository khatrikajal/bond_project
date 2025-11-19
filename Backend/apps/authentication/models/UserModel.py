from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, mobile_number, email=None, password=None, **extra_fields):
        if not mobile_number:
            raise ValueError("Mobile number required")

        email = self.normalize_email(email) if email else None

        user = self.model(email=email, mobile_number=mobile_number, **extra_fields)
        if password:
            user.set_password(password)   # Django salted hash
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(mobile_number, email, password, **extra_fields)








class UserRole(models.TextChoices):
    ISSUER = "ISSUER", "Issuer"
    TRUSTEE = "TRUSTEE", "Trustee"
    INVESTOR = "INVESTOR", "Investor"


class User(AbstractBaseUser, PermissionsMixin):
    mobile_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)

    mobile_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.INVESTOR
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = ["email"]





