from beowulf.amount import Amount
from rest_framework import serializers

from api.models import Account
from beowulf.account import Account as BeoAccount


class AccountSerializer(serializers.ModelSerializer):
    available_capacity = serializers.SerializerMethodField()
    maintenance_fee = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    w_balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('account_name', 'email', 'total_capacity', 'used_capacity', 'available_capacity', 'balance',
                  'w_balance', 'maintenance_fee', 'expired_maintain')

    def get_available_capacity(self, obj):
        return obj.get_available_capacity()

    def get_maintenance_fee(self, obj):
        return obj.get_maintenance_fee()

    def get_balance(self, obj):
        beowulf_account = BeoAccount(obj.account_name)
        return Amount(beowulf_account['balance']).amount

    def get_w_balance(self, obj):
        beowulf_account = BeoAccount(obj.account_name)
        return Amount(beowulf_account['wd_balance']).amount
