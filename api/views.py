import datetime
import logging

import hashlib
import json
import os
from django.db import transaction
from rest_framework import status

from rest_framework.views import APIView
from rest_framework.response import Response

from api.serializers import PurchaseSerializer, AccountSerializer
from beowulf_connector import settings
from beowulf_connector.wsgi import commit, creator
from api.models import Account, Transfer, Purchase

from wallet_file.wallet_file import wallet_dir


_logger = logging.getLogger('api')

class AccountView(APIView):
    """
    get:
        Get account information
    post:
        Create a new account instance.
    """

    def get(self, request):
        try:
            account_name = request.query_params.get('account_name')
            account = Account.objects.filter(username=account_name)

            serializer = AccountSerializer(account, many=True)
            return Response(data={"msg": 'Success!', "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(data={"msg": repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data
            username = request_data.get('username')
            password = request_data.get('password')
            email = request_data.get('email')
            host = request_data.get('hostIP')

            password = hashlib.sha256(password.encode()).hexdigest()
            Account.objects.create(username=username, password=password, email=email, host=host)

            data = commit.create_account_simple(account_name=username,
                                                creator=creator,
                                                password_seed="password",
                                                password_wallet=password)

            wallet_filename = os.path.join(wallet_dir, username + ".json")

            with open(wallet_filename) as json_data:
                cipher_data = json.load(json_data)

            data["wallet"] = cipher_data

            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            _logger.exception('[Create Account] Error: ')
            return Response(data={"msg": repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransferView(APIView):
    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data

            sender = request_data.get('sender')
            receiver = request_data.get('receiver')
            amount = request_data.get('amount')
            memo = request_data.get('memo')
            asset = request_data.get('asset')

            fee = settings.TRANSFER_FEE
            asset_fee = settings.TRANSFER_ASSET_FEE

            Transfer.objects.create(sender=sender, receiver=receiver, amount=amount, memo=memo, asset=asset)

            data = commit.transfer(receiver, amount, asset, fee, asset_fee, memo, sender)

            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            return Response(data={"msg": repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PurchaseView(APIView):
    """
    get:
        Get all purchase or get purchase by account_name.
    post:
        Create a new account instance.
    """

    def get(self, request):
        try:
            account_name = request.query_params.get('account_name')
            purchases = Purchase.objects.all()

            if account_name:
                account_name = account_name.split(',')
                purchases = purchases.filter(account_name__in=account_name)

            serializer = PurchaseSerializer(purchases, many=True)
            return Response(data={"msg": 'Success!', "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(data={"msg": repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data

            account_name = request_data.get('sender')
            receiver = creator
            amount = request_data.get('amount')
            memo = request_data.get('memo')
            asset = settings.PURCHASE_ASSET
            fee = settings.TRANSFER_FEE
            asset_fee = settings.TRANSFER_ASSET_FEE

            # Create Transfer for Purchase
            Transfer.objects.create(sender=account_name, receiver=receiver, amount=amount, memo=memo, asset=asset)

            # Create Purchase, get surplus if purchase is already exists, add surplus to amount
            purchase = Purchase.objects.get_or_create(account_name=account_name)
            amount += (purchase.surplus or 0)

            purchase_amount = settings.PURCHASE_AMOUNT
            surplus = amount % purchase_amount
            expired_date = datetime.datetime.now() + datetime.timedelta(days=(30 * int(amount / purchase_amount)))
            purchase.surplus = surplus
            purchase.expired_date = expired_date
            purchase.save()

            # Create Beowulf Transfer
            data = commit.transfer(receiver, amount, asset, fee, asset_fee, memo, account_name)
            data['expired_date'] = expired_date

            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            _logger.exception('[Create Purchase] Error: ')
            return Response(data={"msg": repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
