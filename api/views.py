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
from api.models import Account, Transfer, Purchase, Price

from wallet_file.wallet_file import wallet_dir


_logger = logging.getLogger('api')


class AccountView(APIView):
    def get(self, request):
        try:
            account_name = request.query_params.get('account_name')
            account = Account.objects.filter(account_name=account_name)

            serializer = AccountSerializer(account, many=True)
            return Response(data={"msg": 'Success!', "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(data={"msg": repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data
            account_name = request_data.get('account_name')
            password = request_data.get('password')
            email = request_data.get('email')
            host = request_data.get('hostIP')

            password = hashlib.sha256(password.encode()).hexdigest()
            Account.objects.create(account_name=account_name, password=password, email=email, host=host)

            data = commit.create_account_simple(account_name=account_name,
                                                creator=creator,
                                                password_seed="password",
                                                password_wallet=password)

            wallet_filename = os.path.join(wallet_dir, account_name + ".json")

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
            try:
                account = Account.objects.get(account_name=account_name)
            except Account.DoesNotExist:
                return Response(data={"msg": "Account does not exists!"}, status=status.HTTP_404_NOT_FOUND)

            admin_account = creator
            code = request_data.get('code')
            memo = request_data.get('memo')
            asset = settings.PURCHASE_ASSET
            asset_fee = settings.TRANSFER_ASSET_FEE

            price = Price.get_price(code)
            amount = price.amount
            if account.get_balance() < amount:
                return Response(data={"msg": "Account balance is not enough"}, status=status.HTTP_406_NOT_ACCEPTABLE)

            Transfer.objects.create(sender=account_name, receiver=admin_account, amount=amount, memo=memo, asset=asset)
            data = commit.transfer(admin_account, amount, asset, 0, asset_fee, memo, account_name)

            account.total_capacity = price.capacity
            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            _logger.exception('[Create Purchase] Error: ')
            return Response(data={"msg": repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PurchaseMaintenanceView(APIView):
    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data

            _account_name = request_data.get('sender')
            try:
                account = Account.objects.get(account_name=_account_name)
            except Account.DoesNotExist:
                return Response(data={"msg": "Account does not exists!"}, status=status.HTTP_404_NOT_FOUND)

            admin_account = creator
            memo = request_data.get('memo')
            asset = settings.PURCHASE_ASSET
            asset_fee = settings.TRANSFER_ASSET_FEE

            maintain_fee = account.get_maintenance_fee()
            if account.get_balance() < maintain_fee:
                return Response(data={"msg": "Account balance is not enough"}, status=status.HTTP_406_NOT_ACCEPTABLE)

            Transfer.objects.create(sender=_account_name, receiver=admin_account, amount=maintain_fee, memo=memo,
                                    asset=asset)

            data = commit.transfer(admin_account, maintain_fee, asset, 0, asset_fee, memo, _account_name)

            account.update_maintenance_duration()
            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            _logger.exception('[Create Purchase] Error: ')
            return Response(data={"msg": repr(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
