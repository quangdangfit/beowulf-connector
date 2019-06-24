from rest_framework import serializers

from api.models import Purchase, Account
from beowulf_connector import settings


class AccountSerializer(serializers.ModelSerializer):
    available_capacity = serializers.SerializerMethodField()
    maintain_fee = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('username', 'email', 'capacity', 'used_capacity', 'available_capacity', 'expired_maintain')

    def get_available_capacity(self, obj):
        return obj.capacity - obj.used_capacity

    def get_maintain_fee(self, obj):
        return obj.used_capacity * settings.MAINTAIN_FREE

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ('account_name', 'expired_date', 'surplus')
