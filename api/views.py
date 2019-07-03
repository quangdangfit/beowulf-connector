import logging

import hashlib
import json
import os
from beowulf.amount import Amount
from django.db import transaction
from rest_framework import status

from rest_framework.views import APIView
from rest_framework.response import Response

from api.serializers import AccountSerializer
from api.utils import randomString, generateAccountName
from beowulf_connector import settings
from beowulf_connector.beowulf import commit, creator
from api.models import Account, Transfer, Price

from wallet_file.wallet_file import wallet_dir


_logger = logging.getLogger('api')


class AccountView(APIView):
    def get(self, request):
        try:
            email = request.query_params.get('email')
            account = Account.objects.filter(email=email)

            serializer = AccountSerializer(account, many=True)
            return Response(data={"msg": 'Success!', "error_code": 0, "data": serializer.data},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response(data={"msg": repr(e), "error_code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data
            password = request_data.get('password')
            email = request_data.get('email')
            worker_id = request_data.get('worker_id')
            account_name = generateAccountName(worker_id=worker_id)

            password = hashlib.sha256(password.encode()).hexdigest()

            data = commit.create_account_simple(account_name=account_name,
                                                creator=creator,
                                                password_seed="password",
                                                password_wallet=password)

            Account.objects.create(account_name=account_name, password=password, email=email, worker_id=worker_id)

            wallet_filename = os.path.join(wallet_dir, account_name + ".json")

            with open(wallet_filename) as json_data:
                cipher_data = json.load(json_data)

            data["wallet"] = cipher_data

            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "error_code": 0, "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            _logger.exception('[Create Account] Error: ')
            return Response(data={"msg": repr(e), "error_code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, email):
        sid = transaction.savepoint()
        try:
            request_data = request.data
            used_capacity = float(request_data.get('used_capacity', '0'))

            try:
                account = Account.objects.get(email=email)
            except Account.DoesNotExist:
                return Response(data={"msg": "Account does not exists!", "error_code": 404},
                                status=status.HTTP_404_NOT_FOUND)

            if 0 <= used_capacity <= account.total_capacity:
                account.used_capacity = used_capacity
                account.save()
            else:
                return Response(data={"msg": "Used capacity must be less than total capacity!"},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "error_code": 0}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            _logger.exception('[Update Account] Error: ')
            return Response(data={"msg": repr(e), "error_code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response(data={"msg": 'Success!', "error_code": 0, "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            return Response(data={"msg": repr(e), "error_code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PurchaseView(APIView):
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
            memo = "Purchase Capacity"
            asset = settings.PURCHASE_ASSET

            fee = settings.TRANSFER_FEE
            asset_fee = settings.TRANSFER_ASSET_FEE

            price = Price.get_price(code)
            amount = price.amount

            from beowulf.account import Account as BeoAccount

            beowulf_account = BeoAccount(account_name)
            if beowulf_account and amount > Amount(beowulf_account['balance']).amount:
                return Response(data={"msg": 'Balance is not enough!', "error_code": 406},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

            data = commit.transfer(admin_account, amount, asset, fee, asset_fee, memo, account_name)
            Transfer.objects.create(sender=account_name, receiver=admin_account, amount=amount, memo=memo, asset=asset)

            account.total_capacity = price.capacity
            account.save()
            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "error_code": 0, "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            _logger.exception('[Create Purchase] Error: ')
            return Response(data={"msg": repr(e), "error_code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PurchaseMaintenanceView(APIView):
    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data

            sender_email = request_data.get('email')
            try:
                account = Account.objects.get(email=sender_email)
            except Account.DoesNotExist:
                return Response(data={"msg": "Account does not exists!"}, status=status.HTTP_404_NOT_FOUND)

            admin_account = creator
            sender_account_name = account.account_name
            memo = "Purchase Maintenance"
            asset = settings.PURCHASE_ASSET

            fee = settings.TRANSFER_FEE
            asset_fee = settings.TRANSFER_ASSET_FEE

            maintenance_fee = account.get_maintenance_fee()
            data = commit.transfer(admin_account, maintenance_fee, asset, fee, asset_fee, memo, sender_account_name)
            Transfer.objects.create(sender=sender_account_name, receiver=admin_account, amount=maintenance_fee,
                                    memo=memo, asset=asset)

            account.update_maintenance_duration()
            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "error_code": 0, "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            _logger.exception('[Create Purchase Maintenance] Error: ')
            return Response(data={"msg": repr(e), "error_code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
