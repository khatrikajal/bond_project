from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone



class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):

    def create_user(self, email, mobile_number=None, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(email=email, mobile_number=mobile_number, **extra_fields)

        if password:
            user.set_password(password)

        user.save(using=self._db)

        # assign single role if provided
        if role:
            user.roles.add(role)

        return user

    def create_superuser(self, email, mobile_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, mobile_number, password, **extra_fields)




class User(AbstractBaseUser, PermissionsMixin):
    mobile_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)

    mobile_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    roles = models.ManyToManyField(Role, related_name="users")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["mobile_number"]





