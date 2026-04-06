from django.db import models


class Customer(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=30, blank=True)
    language = models.CharField(max_length=8, blank=True)
    currency = models.CharField(max_length=8, blank=True)
    wishlist = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)
