from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ('doctor', 'Doctor'),
        ('user', 'User'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Height in centimeters

    def __str__(self):
        return f'{self.user.username} - {self.get_user_type_display()}'