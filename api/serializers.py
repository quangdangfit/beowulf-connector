from rest_framework import serializers

from api.models import Account


class AccountSerializer(serializers.ModelSerializer):
    available_capacity = serializers.SerializerMethodField()
    maintenance_fee = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('account_name', 'email', 'total_capacity', 'used_capacity', 'available_capacity', 'maintenance_fee',
                  'expired_maintain')

    def get_available_capacity(self, obj):
        return obj.get_available_capacity()

    def get_maintenance_fee(self, obj):
        return obj.get_maintenance_fee()
