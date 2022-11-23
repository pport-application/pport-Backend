from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from decouple import config
import urllib.request
from urllib.error import URLError, HTTPError
import json

from datetime import datetime, timedelta


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAdminUser])
def delete_reset_codes(_):
    my_client = MongoClient(config("MONGO_CLIENT"))

    past_date_after_1hour = (datetime.now() - timedelta(hours=1)).strftime("%d/%m/%Y %H:%M:%S")
    my_client.pport.reset_password_requests.delete_many({"sent_time": {"$lt": past_date_after_1hour}})

    my_client.close()
    return Response(status=status.HTTP_200_OK)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAdminUser])
def update_database(_):
    my_client = MongoClient(config("MONGO_CLIENT"))

    users = my_client.pport.users.find({}, {"email": 1, "password": 1, "_id": 0})

    User.objects.all().delete()
    Token.objects.all().delete()

    for row in users:
        user = User.objects.create_user(username=row["email"], password=row["password"])
        Token.objects.create(user=user)

    my_client.close()
    return Response(status=status.HTTP_200_OK)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAdminUser])
def update_mongo(_):
    my_client = MongoClient(config("MONGO_CLIENT"))

    # Check for history objects, if not found instance of user then add.
    users = my_client.pport.users.aggregate([{"$lookup": {"from": "history", "localField": "_id", "foreignField": "user_id", "as": "join"}},
                                             {"$match": {"join": {"$size": 0}}},
                                             {"$project": {"user_id": 1}}])
    for user_id in users:
        my_dict = {"user_id": user_id["_id"], "history": []}
        my_client.pport.history.insert_one(my_dict)

    # Check for portfolio objects, if not found instance of user then add.
    users = my_client.pport.users.aggregate([{"$lookup": {"from": "portfolio", "localField": "_id", "foreignField": "user_id", "as": "join"}},
                                             {"$match": {"join": {"$size": 0}}},
                                             {"$project": {"user_id": 1}}])
    for user_id in users:
        my_dict = {"user_id": user_id["_id"], "portfolio": [], "wallet": {}}
        my_client.pport.portfolio.insert_one(my_dict)

    # Remove instances of user that no longer exists
    # noinspection DuplicatedCode
    users = my_client.pport.history.aggregate([{"$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "join"}},
                                               {"$match": {"join": {"$size": 0}}},
                                               {"$project": {"user_id": 1}}])

    res = []
    for user_id in users:
        res.append(user_id["user_id"])
    if len(res) > 0:
        my_client.pport.history.delete_many({"user_id": {"$in": res}})

    # noinspection DuplicatedCode
    users = my_client.pport.portfolio.aggregate([{"$lookup": {"from": "users", "localField": "user_id", "foreignField": "_id", "as": "join"}},
                                                 {"$match": {"join": {"$size": 0}}},
                                                 {"$project": {"user_id": 1}}])
    res = []
    for user_id in users:
        res.append(user_id["user_id"])
    if len(res) > 0:
        my_client.pport.portfolio.delete_many({"user_id": {"$in": res}})

    my_client.close()
    return Response(status=status.HTTP_200_OK)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAdminUser])
def update_exchanges(_):
    my_client = MongoClient(config("MONGO_CLIENT"))
    eod_url = config("EOD_URL") + "exchanges-list/?api_token=" + config("EOD_API_KEY") + "&fmt=json"
    try:
        http_request = urllib.request.urlopen(eod_url).read()
        data = json.loads(http_request.decode('utf-8'))
        my_client.pport.exchanges.drop()
        my_client.pport.exchanges.insert_many(data)
        my_client.close()
        return Response(status=status.HTTP_200_OK)
    except HTTPError:
        return Response({"error": "HTTP Error."}, status=status.HTTP_400_BAD_REQUEST)
    except URLError:
        return Response({"error": "URL Error."}, status=status.HTTP_400_BAD_REQUEST)
    my_client.close()
    return Response(status=status.HTTP_200_OK)