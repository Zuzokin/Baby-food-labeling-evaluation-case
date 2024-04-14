from django.db import models

# Create your models here.
class UploadFiles(models.Model):
    file = models.FileField(upload_to='upload_model')