from rest_framework import serializers

from api.models import Purchase, Account


class AccountSerializer(serializers.ModelSerializer):
    available_capacity = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('username', 'email', 'capacity', 'used_capacity', 'available_capacity', 'expired_maintain')

    def get_available_capacity(self, obj):
        return obj.capacity - obj.used_capacity

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ('account_name', 'expired_date', 'surplus')
