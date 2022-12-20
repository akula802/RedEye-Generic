# Core library imports

# 3rd-party imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# 3rd-party imports
import json
import requests

# Local app imports
from .models import LobServers
from .serializers import Api_LobServers_serializer


############################


class lob_servers(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = LobServers.objects.all()
        serializer = Api_LobServers_serializer(queryset, many=True)
        #serializer = {'message': 'Hello, guy'}
        #return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.data)

