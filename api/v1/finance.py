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
    if request.GET.get("exchange_code") is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    exchange_code = request.GET.get("exchange_code")

    eod_url = config("EOD_URL") + "exchange-symbol-list/" + exchange_code + "?api_token=" + config("EOD_API_KEY") + "&fmt=json"

    try:
        http_request = urllib.request.urlopen(eod_url)
        data = json.loads(http_request.read())
        return Response({"data", str(data)}, status=status.HTTP_200_OK)
    except HTTPError:
        return Response({"error": "HTTP Error."}, status=status.HTTP_400_BAD_REQUEST)
    except URLError:
        return Response({"error": "URL Error."}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def get_exchange_codes(_):

    eod_url = config("EOD_URL") + "exchanges-list/?api_token=" + config("EOD_API_KEY") + "&fmt=json"

    try:
        http_request = urllib.request.urlopen(eod_url)
        data = json.loads(http_request.read())
        us_exchanges = ["NYSE", "NASDAQ", "BATS", "OTCQB", "PINK", "OTCQX", "OTCMKTS", "NMFQS", "NYSE MKT", "OTCBB", "OTCGREY", "BATS", "OTC"]

        for item in us_exchanges:
            data.append({
                "Name": item,
                "Code": "US",
                "OperatingMIC": None,
                "Country": "USA",
                "Currency": "USD"
            })
        data.pop(0)
        return Response({"data", str(data)}, status=status.HTTP_200_OK)
    except HTTPError:
        return Response({"error": "HTTP Error."}, status=status.HTTP_400_BAD_REQUEST)
    except URLError:
        return Response({"error": "URL Error."}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def get_currency_codes(_):

    eod_url = config("EOD_URL") + "exchange-symbol-list/FOREX?api_token=" + config("EOD_API_KEY") + "&fmt=json"

    try:
        http_request = urllib.request.urlopen(eod_url)
        data = json.loads(http_request.read())
        currencies = []
        for item in data:
            if len(item["Code"]) == 3:
                currencies.append(item)
        return Response({"data": str(currencies), "row": str(data)}, status=status.HTTP_200_OK)
    except HTTPError:
        return Response({"error": "HTTP Error."}, status=status.HTTP_400_BAD_REQUEST)
    except URLError:
        return Response({"error": "URL Error."}, status=status.HTTP_400_BAD_REQUEST)
