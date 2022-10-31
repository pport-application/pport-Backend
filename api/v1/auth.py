from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from bson.objectid import ObjectId
from decouple import config

import uuid
from datetime import datetime, timedelta
import random
import smtplib
import ssl


@api_view(["POST", ])
def sign_in(request):
    if request.GET.get("email") is None or request.GET.get("password") is None:
        return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

    email = str(request.GET.get("email"))
    password = str(request.GET.get("password"))

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"email": email, "password": password}):
        my_client.pport.users.update_one({"email": email}, {"$set": {"session": str(uuid.uuid1())}})
        item = my_client.pport.users.find_one({"email": email, "password": password})
        my_client.close()

        return Response({"user_id": str(item.get("_id")),
                         "session": item.get("session"),
                         "name": item.get("name"),
                         "surname": item.get("surname"),
                         "watchlist": item.get("watchlist")}, status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid username or password"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST", ])
def sign_out(request):
    if request.GET.get("user_id") is None or request.GET.get("session") is None:
        return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

    user_id = request.GET.get("user_id")
    obj_instance = ObjectId(user_id)
    session = request.GET.get("session")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"_id": obj_instance, "session": session}):
        my_client.pport.users.update_one({"_id": obj_instance}, {"$unset": {"session": 1}})
        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid user_id or session"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST", ])
def sign_up(request):
    if request.GET.get("name") is None \
            or request.GET.get("surname") is None \
            or request.GET.get("email") is None \
            or request.GET.get("password") is None:
        return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

    name = request.GET.get("name")
    surname = request.GET.get("surname")
    email = request.GET.get("email")
    password = request.GET.get("password")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"email": email}):
        my_client.close()
        return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

    my_dict = {"name": name, "surname": surname, "email": email, "password": password, "watchlist": []}
    my_client.pport.users.insert_one(my_dict)
    user = my_client.pport.users.find_one({"email": email})
    user_id = user["_id"]

    my_dict = {"user_id": user_id, "all_history": []}
    my_client.pport.history.insert_one(my_dict)

    my_dict = {"user_id": user_id, "portfolio": [], "profit": 0, "wallet": {}}
    my_client.pport.portfolio.insert_one(my_dict)
    my_client.close()

    user = User.objects.create_user(username=email, password=password)
    Token.objects.create(user=user)

    return Response(status=status.HTTP_200_OK)


@api_view(["POST", ])
def reset_password(request):
    if request.GET.get("email") is None:
        return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

    email = request.GET.get("email")

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"email": email}):
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        reset_code = random.randint(1000, 9999)

        my_dict = {"email": email, "sent_time": dt_string, "reset_code": reset_code}
        my_client.pport.reset_password_requests.insert_one(my_dict)
        my_client.close()

        # mail service
        port = config("SSL_PORT", cast=int)
        smtp_server = config("SMTP_SERVER")
        sender_email = config("PPORT_EMAIL")
        receiver_email = email
        password = config("PPORT_EMAIL_PASSWORD")
        message = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n Please enter the following number in pport to reset your password within 15 minutes : %d" % (
            "pport.application@gmail.com", email, "PPORT Password Reset Request", reset_code)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid user_id or session"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST", ])
def validate_reset_code(request):
    if request.GET.get("email") is None or request.GET.get("reset_code") is None:
        return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

    email = request.GET.get("email")
    reset_code = request.GET.get("reset_code")

    try:
        reset_code = int(reset_code)
    except (TypeError, ValueError):
        return Response({"error": "Please provide integer for reset code"}, status=status.HTTP_400_BAD_REQUEST)

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.reset_password_requests.find_one({"email": email}):
        my_query = {"email": email, "reset_code": int(reset_code)}
        my_doc = my_client.pport.reset_password_requests.find(my_query)
        for x in my_doc:
            sent_request_time = datetime.strptime(x["sent_time"], "%d/%m/%Y %H:%M:%S")
            # Calculating the 15 minutes gap
            future_date_after_15minutes = sent_request_time + timedelta(minutes=15)
            if datetime.now() <= future_date_after_15minutes:
                my_client.close()
                return Response(status=status.HTTP_200_OK)

        my_client.close()
        return Response({"error": "Please try password reset again."}, status=status.HTTP_400_BAD_REQUEST)

    my_client.close()
    return Response({"error": "Invalid user_id or session"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST", ])
def change_password(request):
    if request.GET.get("email") is None \
            or request.GET.get("reset_code") is None \
            or request.GET.get("password") is None:
        return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

    email = request.GET.get("email")
    reset_code = request.GET.get("reset_code")
    new_password = request.GET.get("password")

    try:
        reset_code = int(reset_code)
    except (TypeError, ValueError):
        return Response({"error": "Please provide integer for reset code"}, status=status.HTTP_400_BAD_REQUEST)

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.reset_password_requests.find_one({"email": email}):
        my_query = {"email": email, "reset_code": reset_code}
        my_doc = my_client.pport.reset_password_requests.find(my_query)
        now = datetime.now()
        for x in my_doc:
            sent_request_time = datetime.strptime(x["sent_time"], "%d/%m/%Y %H:%M:%S")
            future_date_after_15minutes = sent_request_time + timedelta(minutes=15)
            if now <= future_date_after_15minutes:
                my_client.pport.users.update_one({"email": email}, {"$set": {"password": new_password}})
                my_client.pport.reset_password_requests.delete_many({"email": email})
                user = User.objects.filter(username__icontains=email)[0]
                user.set_password(new_password)
                user.save()
                token = Token.objects.get(user=user)
                token.delete()
                Token.objects.create(user=user)
                my_client.close()
                return Response(status=status.HTTP_200_OK)

        my_client.close()
        return Response({"error": "Please try password reset again.", "my_doc": my_doc, "reset_code": reset_code}, status=status.HTTP_400_BAD_REQUEST)

    my_client.close()
    return Response({"error": "Invalid user_id or session"}, status=status.HTTP_404_NOT_FOUND)


