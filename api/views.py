import hashlib
import json
import os
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response

from beowulf_connector.wsgi import commit, creator
from api.models import Account, Transfer


class AccountView(APIView):
    def post(self, request):
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

            from wallet_file.wallet_file import wallet_dir
            wallet_filename = os.path.join(wallet_dir, username + ".json")

            with open(wallet_filename) as json_data:
                cipher_data = json.load(json_data)

            data["wallet"] = cipher_data
            return JsonResponse(data)

        except Exception as e:
            return Response(data={"msg": repr(e)}, status=500)


class TransferView(APIView):
    def post(self, request):
        try:
            _data = request.data
            sender = _data.get('sender')
            receiver = _data.get('receiver')
            amount = _data.get('amount')
            memo = _data.get('memo')
            asset = _data.get('asset')

            transfer = Transfer.objects.create(sender=sender, receiver=receiver, amount=amount, memo=memo, asset=asset)
        except Exception as e:
            return Response(repr(e))

        return Response('POST Account!')
