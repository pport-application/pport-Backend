from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import urllib.request
from urllib.error import URLError, HTTPError
import json


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def get_tickers(request):
    body = json.loads(request.body)
    if body["session"] is None or body["exchange_code"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)
    
    session = body["session"]
    exchange_code = body["exchange_code"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        my_client.close()
        eod_url = config("EOD_URL") + "exchange-symbol-list/" + exchange_code + "?api_token=" + config("EOD_API_KEY") + "&fmt=json"
        try:
            http_request = urllib.request.urlopen(eod_url).read()
            data = json.loads(http_request.decode('utf-8'))
            return Response(data, status=status.HTTP_200_OK)
        except HTTPError:
            return Response({"error": "HTTP Error."}, status=status.HTTP_400_BAD_REQUEST)
        except URLError:
            return Response({"error": "URL Error."}, status=status.HTTP_400_BAD_REQUEST)
    
    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)

@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def get_exchange_codes(request):
    body = json.loads(request.body)
    if body["session"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)
    
    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        my_client.close()
        eod_url = config("EOD_URL") + "exchanges-list/?api_token=" + config("EOD_API_KEY") + "&fmt=json"
        try:
            http_request = urllib.request.urlopen(eod_url).read()
            data = json.loads(http_request.decode('utf-8'))
            return Response(data, status=status.HTTP_200_OK)
        except HTTPError:
            return Response({"error": "HTTP Error."}, status=status.HTTP_400_BAD_REQUEST)
        except URLError:
            return Response({"error": "URL Error."}, status=status.HTTP_400_BAD_REQUEST)
        
    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)

@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def get_currency_codes(request):
    body = json.loads(request.body)
    if body["session"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)
    
    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        my_client.close()
        eod_url = config("EOD_URL") + "exchange-symbol-list/FOREX?api_token=" + config("EOD_API_KEY") + "&fmt=json"
        try:
            http_request = urllib.request.urlopen(eod_url)
            data = json.loads(http_request.read())
            return Response(data, status=status.HTTP_200_OK)
        except HTTPError:
            return Response({"error": "HTTP Error."}, status=status.HTTP_400_BAD_REQUEST)
        except URLError:
            return Response({"error": "URL Error."}, status=status.HTTP_400_BAD_REQUEST)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)
