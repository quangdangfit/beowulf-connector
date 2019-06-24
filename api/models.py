import datetime

from django.db import models


# Create your models here.
class Account(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    host = models.CharField(max_length=50, unique=True, null=True)
    total_capacity = models.FloatField(default=0)
    used_capacity = models.FloatField(default=0)
    expired_maintain = models.DateTimeField(default=datetime.datetime.now())

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
        return "Transfer {0} to {1}".format(self.sender, self.receiver)

    class Meta:
        db_table = 'transfers'
        ordering = ['id']


class Purchase(models.Model):
    account_name = models.CharField(max_length=50)
    surplus = models.IntegerField(default=0)
    expired_date = models.DateTimeField()

    def __str__(self):
        return "Purchase {}".format(self.account_name)

    class Meta:
        db_table = 'purchases'
        ordering = ['id']


class Price(models.Model):
    amount = models.IntegerField(default=0)
    capacity = models.IntegerField(default=0)

    def __str__(self):
        return "Prices {0} - {1}".format(self.amount, self.capacity)

    class Meta:
        db_table = 'prices'
        ordering = ['id']
