import datetime

from django.db import models

# Create your models here.
from beowulf_connector import settings
from beowulf_connector.wsgi import commit


class Account(models.Model):
    account_name = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    host = models.CharField(max_length=50, unique=True, null=True)
    total_capacity = models.FloatField(default=0)
    used_capacity = models.FloatField(default=0)
    expired_maintain = models.DateTimeField(default=datetime.datetime.now())

    def __str__(self):
        return self.account_name

    class Meta:
        db_table = 'accounts'
        ordering = ['id']

    def get_balance(self):
        beowulf_account = commit.beowulfd.get_account(account=self.account_name)
        return beowulf_account

    def get_available_capacity(self):
        return self.total_capacity - self.used_capacity

    def get_maintain_fee(self):
        return self.used_capacity * settings.MAINTAIN_FREE

    def update_maintain_duration(self):
        maintain_duration = settings.MAINTAIN_DURATION * 30
        if self.expired_maintain < datetime.datetime.now():
            self.expired_maintain = datetime.datetime.now() + datetime.timedelta(days=maintain_duration)
        else:
            self.expired_maintain += datetime.timedelta(days=maintain_duration)
        self.save()

    def extend_maintenance(self):
        maintain_amount = self.get_maintain_fee()
        if self.get_balance() < maintain_amount:
            return False
        self.update_maintain_duration()
        return maintain_amount

    def purchase_capacity(self, code):
        price = Price.get_price(code)
        amount = price.amount
        if self.get_balance() < amount:
            return False
        self.total_capacity += price.capacity
        self.save()
        return amount


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
    code = models.CharField(max_length=50, unique=True)
    amount = models.IntegerField(default=0)
    capacity = models.IntegerField(default=0)

    def __str__(self):
        return "Prices {0}".format(self.code)

    class Meta:
        db_table = 'prices'
        ordering = ['id']

    @classmethod
    def get_price(cls, code):
        return cls.objects.filter(code=code).first()
