from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=120)
    owner = models.CharField(max_length=80)
    description = models.TextField()

    def __str__(self):
        return self.name


class Account(models.Model):
    owner = models.CharField(max_length=80)
    balance = models.IntegerField(default=1000)

    def __str__(self):
        return f"{self.owner}: {self.balance}"


class Document(models.Model):
    title = models.CharField(max_length=120)
    owner = models.CharField(max_length=80)
    body = models.TextField()

    def __str__(self):
        return self.title
