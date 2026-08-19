from django.contrib.auth.models import AbstractUser
from django.db import models


class Org(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class User(AbstractUser):
    org = models.ForeignKey(Org, on_delete=models.CASCADE, null=True, blank=True)


class Report(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    secret_note = models.TextField()

    def __str__(self):
        return self.title


class Event(models.Model):
    kind = models.CharField(max_length=32)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.kind}] {self.message}"
