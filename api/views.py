from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import Account


class AccountView(APIView):
    def post(self, request):
        return Response('POST Account!')
