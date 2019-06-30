from rest_framework import serializers

from api.models import Account

class AccountSerializer(serializers.ModelSerializer):
    available_capacity = serializers.SerializerMethodField()
    maintain_fee = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('username', 'email', 'total_capacity', 'used_capacity', 'available_capacity', 'maintain_fee',
                  'expired_maintain')

    def get_available_capacity(self, obj):
        return obj.get_available_capacity()

    def get_maintain_fee(self, obj):
        return obj.get_maintain_fee()
