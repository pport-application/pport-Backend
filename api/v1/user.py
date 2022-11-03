from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from bson.objectid import ObjectId
from decouple import config


@csrf_exempt
@api_view(["DELETE", ])
def delete_user(request):
    if request.GET.get("email") is None or request.GET.get("password") is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    email = request.GET.get("email")
    password = request.GET.get("password")

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
@api_view(["GET", ])
def get_user_info(request):
    if request.GET.get("session") is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = request.GET.get("session")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        user = my_client.pport.users.find_one({"session": session})

        my_client.close()
        return Response({"name": user["name"], "surname": user["surname"], "email": user["email"]}, status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
def update_user_info(request):
    if request.GET.get("session") is None \
            or request.GET.get("name") is None \
            or request.GET.get("surname") is None \
            or request.GET.get("email") is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    name = request.GET.get("name")
    surname = request.GET.get("surname")
    email = request.GET.get("email")
    session = request.GET.get("session")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        my_client.pport.users.update_one({"session": session}, {"$set": {"name": name, "surname": surname, "email": email}})

        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
def change_password(request):
    if request.GET.get("session") is None \
            or request.GET.get("old_password") is None \
            or request.GET.get("new_password") is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    old_password = request.GET.get("old_password")
    new_password = request.GET.get("new_password")
    session = request.GET.get("session")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session, "password": old_password}):
        my_client.pport.users.update_one({"session": session}, {"$set": {"password": new_password}})

        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)
