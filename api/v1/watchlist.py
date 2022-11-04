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
def get_watchlist_data(request):
    if request.GET.get("session") is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = request.GET.get("session")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        user = my_client.pport.users.find_one({"session": session})
        tickers_list = user["watchlist"]

        my_client.close()

        if len(tickers_list) == 0:
            return Response({"data", {}}, status=status.HTTP_200_OK)

        eod_url = config("EOD_URL") + "real-time/" + tickers_list[0] + "?api_token=" + config("EOD_API_KEY")

        if len(tickers_list) > 1:
            eod_url += "&fmt=json&s=" + (",".join(tickers_list[1:]))

        try:
            http_request = urllib.request.urlopen(eod_url)
            data = json.loads(http_request.read())
            for item in data:
                for key in item:
                    item[key] = str(item[key])
            return Response({"data", str(data)}, status=status.HTTP_200_OK)
        except HTTPError:
            return Response({"error": "HTTP Error."}, status=status.HTTP_400_BAD_REQUEST)
        except URLError:
            return Response({"error": "URL Error."}, status=status.HTTP_400_BAD_REQUEST)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def delete_watchlist_item(request):
    if request.GET.get("session") is None or request.GET.get("ticker") is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    ticker = request.GET.get("ticker")
    session = request.GET.get("session")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        user = my_client.pport.users.find_one({"session": session})
        my_client.pport.users.update_many(user, {"$pull": {"watchlist": ticker}})

        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def add_watchlist_item(request):
    if request.GET.get("session") is None or request.GET.get("ticker") is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = request.GET.get("session")
    ticker = request.GET.get("ticker")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        my_client.pport.users.update_one({"session": session},
                                         {"$addToSet": {"watchlist": ticker}})

        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)




