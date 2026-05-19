import uuid
from django.db import models
from django.utils import timezone

class UserRegistrationModel(models.Model):
    name          = models.CharField(max_length=100)
    loginid       = models.CharField(unique=True, max_length=100)
    password      = models.CharField(max_length=100)
    mobile        = models.CharField(unique=True, max_length=100)
    email         = models.CharField(unique=True, max_length=100)
    locality      = models.CharField(max_length=100)
    address       = models.CharField(max_length=1000)
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100)
    status        = models.CharField(max_length=100)
    last_login    = models.DateTimeField(null=True, blank=True)
    approve_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.loginid

    class Meta:
        db_table = 'UserRegistrations'


class PasswordResetOTP(models.Model):                          # ← ADD THIS
    user       = models.ForeignKey(UserRegistrationModel, on_delete=models.CASCADE)
    otp        = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)  # OTP valid for 10 mins

    class Meta:
        db_table = 'PasswordResetOTP'


class AcnePredictionModel(models.Model):
    user            = models.ForeignKey(UserRegistrationModel, on_delete=models.CASCADE)
    image           = models.ImageField(upload_to='prediction_images/')
    annotated_image = models.ImageField(upload_to='prediction_images/', null=True, blank=True)
    result          = models.CharField(max_length=100)
    model_name      = models.CharField(max_length=100, null=True, blank=True)
    timestamp       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'AcnePredictions'