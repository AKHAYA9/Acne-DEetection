from django.db import models

class AdminModel(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'Admins'
