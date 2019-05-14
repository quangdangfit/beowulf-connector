from django.db import models


# Create your models here.
class Account(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=100)
    email = models.CharField(max_length=100)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'accounts'
        ordering = ['id']


class Transfer(models.Model):
    sender = models.CharField(max_length=50)
    receiver = models.CharField(max_length=50)
    amount = models.IntegerField(default=0)
    memo = models.TextField()
    asset = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Transfer {} to {}".format(self.sender, self.receiver)

    class Meta:
        db_table = 'transfers'
        ordering = ['id']
