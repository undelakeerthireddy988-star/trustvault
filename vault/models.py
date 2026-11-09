from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='docs/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title