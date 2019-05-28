from rest_framework import serializers

from api.models import Purchase


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ('account_name', 'expired_date', 'surplus')
