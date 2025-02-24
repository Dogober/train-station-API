from django.db import models


class APIUsage(models.Model):
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)  # GET, POST и т.д.
    timestamp = models.DateTimeField(auto_now_add=True)
    response_status = models.IntegerField()
    user_ip = models.GenericIPAddressField()
    objects = models.Manager()

    class Meta:
        ordering = ['-timestamp']
