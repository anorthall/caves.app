from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class CavingUserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None):
        """Creates a CavingUser"""

        if not email:
            raise ValueError("Users must have an email address")

        if not username:
            raise ValueError("Users must have a username")

        if not first_name or not last_name:
            raise ValueError("Users must have a first and last name")

        user = self.model(
            email=self.normalize_email(email),
            username=username.lower(),
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password=None):
        """Creates a CavingUser which is a superuser"""
        user = self.create_user(
            email,
            username,
            first_name,
            last_name,
            password,
        )

        user.is_admin = True
        user.save(using=self._db)
        return user


class CavingUser(AbstractBaseUser):
    email = models.EmailField("email address", max_length=255, unique=True)
    username = models.SlugField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    location = models.CharField(max_length=50, blank=True)
    bio = models.TextField("about me", blank=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField("administrator", default=False)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = CavingUserManager()

    class Meta:
        verbose_name = "user"

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin
