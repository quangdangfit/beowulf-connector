import datetime

import hashlib
import json
import os
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response

from beowulf_connector import settings
from beowulf_connector.wsgi import commit, creator
from api.models import Account, Transfer, Purchase

from wallet_file.wallet_file import wallet_dir


class AccountView(APIView):
    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data
            username = request_data.get('username')
            password = request_data.get('password')
            email = request_data.get('email')

            password = hashlib.sha256(password.encode()).hexdigest()
            Account.objects.create(username=username, password=password, email=email)

            data = commit.create_account_simple(account_name=username,
                                                creator=creator,
                                                password_seed="password",
                                                password_wallet=password)

            wallet_filename = os.path.join(wallet_dir, username + ".json")

            with open(wallet_filename) as json_data:
                cipher_data = json.load(json_data)

            data["wallet"] = cipher_data

            transaction.savepoint_commit(sid)
            return Response(data={"msg": 'Success!', "data": data})

        except Exception as e:
            transaction.savepoint_rollback(sid)
            return Response(data={"msg": repr(e)}, status=500)


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
            return Response(data={"msg": 'Success!', "data": data})

        except Exception as e:
            transaction.savepoint_rollback(sid)
            return Response(data={"msg": repr(e)}, status=500)


class PurchaseView(APIView):
    def post(self, request):
        sid = transaction.savepoint()
        try:
            request_data = request.data

            account_name = request_data.get('sender')
            receiver = settings.CREATOR_NAME
            amount = request_data.get('amount')
            memo = request_data.get('memo')
            asset = settings.PURCHASE_ASSET
            fee = settings.TRANSFER_FEE
            asset_fee = settings.TRANSFER_ASSET_FEE

            # Create Transfer for Purchase
            Transfer.objects.create(sender=account_name, receiver=receiver, amount=amount, memo=memo, asset=asset)

            # Create Purchase, get surplus if purchase is already exists, add surplus to amount
            purchase = Purchase.objects.filter(account_name=account_name).first()

            if purchase:
                amount += purchase.surplus
            else:
                purchase = Purchase.objects.create(account_name=account_name)

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
            return Response(data={"msg": 'Success!', "data": data})

        except Exception as e:
            transaction.savepoint_rollback(sid)
            return Response(data={"msg": repr(e)}, status=500)
