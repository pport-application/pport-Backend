from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from bson.objectid import ObjectId
from decouple import config
import json

@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def delete_user(request):
    body = json.loads(request.body)
    if body["email"] is None or body["password"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    email = body["email"]
    password = body["password"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"email": email, "password": password}):
        item = my_client.pport.users.find_one({"email": email, "password": password})
        user_id = str(item.get("_id"))

        my_client.pport.users.delete_one({"_id": ObjectId(user_id)})
        my_client.pport.history.delete_one({"user_id": ObjectId(user_id)})
        my_client.pport.portfolio.delete_one({"user_id": ObjectId(user_id)})

        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response(status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    body = json.loads(request.body)
    if body["session"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        user = my_client.pport.users.find_one({"session": session})

        my_client.close()
        return Response({"name": user["name"], "surname": user["surname"], "email": user["email"]}, status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def update_user_info(request):
    body = json.loads(request.body)
    if body["session"] is None \
            or body["name"] is None \
            or body["surname"] is None \
            or body["email"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    name = body["name"]
    surname = body["surname"]
    email = body["email"]
    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        my_client.pport.users.update_one({"session": session}, {"$set": {"name": name, "surname": surname, "email": email}})

        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def change_password(request):
    body = json.loads(request.body)
    if body["session"] is None \
            or body["old_password"] is None \
            or body["new_password"] is None \
            or body["new_password_confirm"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    old_password = body["old_password"]
    new_password = body["new_password"]
    new_password_confirm = body["new_password_confirm"]
    session = body["session"]

    if new_password != new_password_confirm:
        return Response({"error": "Password mismatch."}, status=status.HTTP_400_BAD_REQUEST)

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session, "password": old_password}):
        user = my_client.pport.users.find_one_and_update({"session": session}, {"$set": {"password": new_password}}, {"email": 1})

        my_client.close()

        user = User.objects.filter(username__icontains=user["email"])[0]
        user.set_password(new_password)
        user.save()
        token = Token.objects.get(user=user)
        token.delete()
        Token.objects.create(user=user)

        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)
