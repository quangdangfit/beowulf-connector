from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import Account, Transfer


class AccountView(APIView):
    def post(self, request):
        try:
            _data = request.data
            username = _data.get('username')
            email = _data.get('email')

            account = Account.objects.create(username=username, email=email)
        except Exception as e:
            return Response(repr(e))

        return Response('POST Account!')


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
