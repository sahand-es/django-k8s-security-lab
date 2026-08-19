from django.db import models


class Queue(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=140)
    squad = models.CharField(max_length=120)
    member_username = models.CharField(max_length=80)
    dashboard_note = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name


class Ticket(models.Model):
    external_id = models.IntegerField(unique=True)
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name="tickets")
    title = models.CharField(max_length=160)
    summary = models.CharField(max_length=240)
    body = models.TextField(blank=True, default="")
    visible_in_frontend = models.BooleanField(default=True)
    staff_only = models.BooleanField(default=False)
    handoff_note = models.TextField(blank=True, default="")

    def __str__(self):
        return self.title
