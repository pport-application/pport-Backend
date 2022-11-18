import json
from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from decouple import config

import uuid
from datetime import datetime, timedelta
import random
import smtplib
import ssl


@csrf_exempt
@api_view(["POST", ])
def sign_in(request):
    body = json.loads(request.body)
    if body["email"] is None or body["password"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    email = body["email"]
    password = body["password"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"email": email, "password": password}):

        session = str(uuid.uuid1())
        for i in range(5):
            if not my_client.pport.users.find_one({"session": session}):
                my_client.pport.users.update_one({"email": email}, {"$set": {"session": session}})
                item = my_client.pport.users.find_one({"email": email, "password": password})
                my_client.close()

                user = User.objects.filter(username__icontains=email)[0]
                try:
                    Token.objects.filter(user=user).delete()
                except (AttributeError, ObjectDoesNotExist):
                    pass
                token = Token.objects.create(user=user)

                return Response({"name": item.get("name"),
                                 "surname": item.get("surname"),
                                 "email": item.get("email"),
                                 "session": item.get("session"),
                                 "watchlist": item.get("watchlist"),
                                 "token": str(token)}, status=status.HTTP_200_OK)
            session = str(uuid.uuid1())
        return Response({"error": "Unable to create session."}, status=status.HTTP_400_BAD_REQUEST)

    my_client.close()
    return Response({"error": "Invalid username or password"}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def sign_out(request):
    body = json.loads(request.body)
    if body["session"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        email = my_client.pport.users.find_one({"session": session}, {"email": 1, "_id": 0})["email"]
        my_client.pport.users.update_one({"session": session}, {"$unset": {"session": 1}})

        my_client.close()

        user = User.objects.filter(username__icontains=email)[0]
        try:
            Token.objects.filter(user=user).delete()
        except (AttributeError, ObjectDoesNotExist):
            pass

        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(["POST", ])
def sign_up(request):
    body = json.loads(request.body)
    if body["name"] is None \
            or body["surname"] is None \
            or body["email"] is None \
            or body["password"] is None \
            or body["password_confirm"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(body, status=status.HTTP_200_OK)
    name = body["name"]
    surname = body["surname"]
    email = body["email"]
    password = body["password"]
    password_confirm = body["password_confirm"]

    if (password != password_confirm):
        return Response({"error": "Password mismatch."}, status=status.HTTP_400_BAD_REQUEST)

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"email": email}):
        my_client.close()
        return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

    my_dict = {"name": name, "surname": surname, "email": email, "password": password, "watchlist": []}
    my_client.pport.users.insert_one(my_dict)
    user = my_client.pport.users.find_one({"email": email})
    user_id = user["_id"]

    my_dict = {"user_id": user_id, "history": []}
    my_client.pport.history.insert_one(my_dict)

    my_dict = {"user_id": user_id, "portfolio": [], "wallet": {}}
    my_client.pport.portfolio.insert_one(my_dict)
    my_client.close()

    user = User.objects.create_user(username=email, password=password)
    Token.objects.create(user=user)

    return Response(status=status.HTTP_200_OK)


@csrf_exempt
@api_view(["POST", ])
def reset_password(request):
    body = json.loads(request.body)
    if body["email"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    email = body["email"]

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
    return Response({"error": "Invalid email address."}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(["POST", ])
def validate_reset_code(request):
    body = json.loads(request.body)
    if body["email"] is None or body["reset_code"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    email = body["email"]
    reset_code = body["reset_code"]

    try:
        reset_code = int(reset_code)
    except (TypeError, ValueError):
        return Response({"error": "Please provide integer for reset code."}, status=status.HTTP_400_BAD_REQUEST)

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


@csrf_exempt
@api_view(["POST", ])
def change_password(request):
    body = json.loads(request.body)
    if body["email"] is None \
            or body["reset_code"] is None \
            or body["new_password"] is None \
            or body["new_password_confirm"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    email = body["email"]
    reset_code = body["reset_code"]
    new_password = body["new_password"]
    new_password_confirm = body["new_password_confirm"]

    if (new_password != new_password_confirm):
        return Response({"error": "Password mismatch."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        reset_code = int(reset_code)
    except (TypeError, ValueError):
        return Response({"error": "Please provide integer for reset code."}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({"error": "Please try password reset again."}, status=status.HTTP_400_BAD_REQUEST)

    my_client.close()
    return Response({"error": "Invalid email address."}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(["POST", ])
def validate_session(request):
    body = json.loads(request.body)
    if body["session"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        return Response(status=status.HTTP_200_OK)

    return Response(status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(["POST", ])
def get_token(request):
    body = json.loads(request.body)
    if body["session"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    if my_client.pport.users.find_one({"session": session}):
        email = my_client.pport.users.find_one({"session": session}, {"email": 1, "_id": 0})["email"]
        my_client.close()

        user = User.objects.filter(username__icontains=email)[0]
        try:
            Token.objects.filter(user=user).delete()
        except (AttributeError, ObjectDoesNotExist):
            pass
        token = Token.objects.create(user=user)

        return Response({"token": str(token)}, status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)
