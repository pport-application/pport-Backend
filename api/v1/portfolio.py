from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from decouple import config
import json

@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def deposit_currency(request):
    body = json.loads(request.body)
    if body["session"] is None \
            or body["currency"] is None \
            or body["amount"] is None \
            or body["timestamp"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    currency = body["currency"]
    amount = body["amount"]
    session = body["session"]
    timestamp = body["timestamp"]

    try:
        amount = float(amount)
        timestamp = int(timestamp)
    except (TypeError, ValueError):
        return Response({"error": "Please provide integer for amount."}, status=status.HTTP_400_BAD_REQUEST)

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        portfolio = my_client.pport.portfolio.find_one({"user_id": user["_id"], "wallet." + currency: {"$exists": 1}},
                                                       {"wallet." + currency: 1, "_id": 0})

        new_amount = amount

        if portfolio is not None:
            new_amount = amount + portfolio["wallet"][currency]

        my_client.pport.portfolio.find_one_and_update({"user_id": user["_id"]},
                                                      {"$set": {"wallet." + currency: new_amount}})

        my_client.pport.history.find_one_and_update({"user_id": user["_id"]},
                                                    {"$push": {"history": {"from": "wallet",
                                                                           "amount": amount,
                                                                           "currency": currency,
                                                                           "type": 1,
                                                                           "balance": new_amount,
                                                                           "timestamp": timestamp}}})
        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def withdraw_currency(request):
    body = json.loads(request.body)
    if body["session"] is None \
            or body["currency"] is None \
            or body["amount"] is None \
            or body["timestamp"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    currency = body["currency"]
    amount = body["amount"]
    session = body["session"]
    timestamp = body["timestamp"]

    try:
        amount = float(amount)
        timestamp = int(timestamp)
    except (TypeError, ValueError):
        return Response({"error": "Please provide integer for amount."}, status=status.HTTP_400_BAD_REQUEST)

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        portfolio = my_client.pport.portfolio.find_one({"user_id": user["_id"], "wallet." + currency: {"$gte": amount}},
                                                       {"wallet." + currency: 1, "_id": 0})

        if portfolio is None:
            my_client.close()
            return Response({"error": "Wallet does not exists or invalid amount requested."},
                            status=status.HTTP_400_BAD_REQUEST)

        new_amount = portfolio["wallet"][currency] - amount

        if new_amount == 0:
            my_client.pport.portfolio.find_one_and_update({"user_id": user["_id"]},
                                                          {"$unset": {"wallet." + currency: 1}})
        else:
            my_client.pport.portfolio.find_one_and_update({"user_id": user["_id"]},
                                                          {"$set": {"wallet." + currency: new_amount}})

        my_client.pport.history.find_one_and_update({"user_id": user["_id"]},
                                                    {"$push": {"history": {"from": "wallet",
                                                                           "amount": amount,
                                                                           "currency": currency,
                                                                           "type": -1,
                                                                           "balance": new_amount,
                                                                           "timestamp": timestamp}}})
        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def get_portfolio(request):
    body = json.loads(request.body)
    if body["session"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        data = my_client.pport.portfolio.find_one({"user_id": user["_id"]}, {"user_id": 0, "_id": 0})

        my_client.close()
        return Response(data, status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def deposit_ticker(request):
    body = json.loads(request.body)
    if body["session"] is None \
            or body["ticker"] is None \
            or body["count"] is None \
            or body["purchase_cost"] is None \
            or body["currency"] is None \
            or body["timestamp"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = body["session"]
    ticker = body["ticker"]
    count = body["count"]
    purchase_cost = body["purchase_cost"]
    currency = body["currency"]
    timestamp = body["timestamp"]

    try:
        count = float(count)
        purchase_cost = -float(purchase_cost)
        timestamp = int(timestamp)
    except (TypeError, ValueError):
        return Response({"error": "Please provide values in valid format."}, status=status.HTTP_400_BAD_REQUEST)

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        portfolio = my_client.pport.portfolio.find_one({"user_id": user["_id"], "portfolio": {"$elemMatch": {"ticker": ticker}}},
                                                       {"portfolio.$": 1, "_id": 0})

        new_balance = purchase_cost

        if portfolio is not None:
            count = count + portfolio["portfolio"][0]["count"]
            new_balance = portfolio["portfolio"][0]["balance"] + purchase_cost
            my_client.pport.portfolio.find_one_and_update({"user_id": user["_id"], "portfolio": {"$elemMatch": {"ticker": ticker}}},
                                                          {"$set": {"portfolio.$":
                                                                        {"ticker": ticker,
                                                                         "count": count,
                                                                         "balance": new_balance,
                                                                         "currency": currency}}})
        else:
            my_client.pport.portfolio.find_one_and_update({"user_id": user["_id"]},
                                                          {"$push": {"portfolio":
                                                                        {"ticker": ticker,
                                                                         "count": count,
                                                                         "balance": purchase_cost,
                                                                         "currency": currency}}})

        my_client.pport.history.find_one_and_update({"user_id": user["_id"]},
                                                    {"$push": {"history": {"from": "portfolio",
                                                                           "ticker": ticker,
                                                                           "count": count,
                                                                           "purchase_cost": purchase_cost,
                                                                           "currency": currency,
                                                                           "type": 1,
                                                                           "balance": new_balance,
                                                                           "timestamp": timestamp}}})

        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def withdraw_ticker(request):
    body = json.loads(request.body)
    if body["session"] is None \
            or body["ticker"] is None \
            or body["count"] is None \
            or body["revenue"] is None \
            or body["currency"] is None \
            or body["timestamp"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = body["session"]
    ticker = body["ticker"]
    count = body["count"]
    revenue = body["revenue"]
    currency = body["currency"]
    timestamp = body["timestamp"]

    try:
        count = float(count)
        revenue = float(revenue)
        timestamp = int(timestamp)
    except (TypeError, ValueError):
        return Response({"error": "Please provide values in valid format."}, status=status.HTTP_400_BAD_REQUEST)

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        portfolio = my_client.pport.portfolio.find_one({"user_id": user["_id"], "portfolio": {"$elemMatch": {"ticker": ticker}}},
                                                       {"portfolio.$": 1, "_id": 0})

        if portfolio is None:
            my_client.close()
            return Response({"error": "Wallet does not exists or invalid amount requested."},
                            status=status.HTTP_400_BAD_REQUEST)

        count = portfolio["portfolio"][0]["count"] - count
        new_balance = portfolio["portfolio"][0]["balance"] + revenue
        if count == 0:
            my_client.pport.portfolio.find_one_and_update({"user_id": user["_id"]},
                                                          {"$pull": {"portfolio": {"ticker": ticker}}})
        else:
            my_client.pport.portfolio.find_one_and_update({"user_id": user["_id"], "portfolio": {"$elemMatch": {"ticker": ticker}}},
                                                          {"$set": {"portfolio.$":
                                                                        {"ticker": ticker,
                                                                         "count": count,
                                                                         "balance": new_balance,
                                                                         "currency": currency}}})

        my_client.pport.history.find_one_and_update({"user_id": user["_id"]},
                                                    {"$push": {"history": {"from": "portfolio",
                                                                           "ticker": ticker,
                                                                           "count": count,
                                                                           "revenue": revenue,
                                                                           "currency": currency,
                                                                           "type": -1,
                                                                           "balance": new_balance,
                                                                           "timestamp": timestamp}}})

        my_client.close()
        return Response(status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(["POST", ])
@permission_classes([IsAuthenticated])
def get_history(request):
    body = json.loads(request.body)
    if body["session"] is None:
        return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)

    session = body["session"]

    my_client = MongoClient(config("MONGO_CLIENT"))

    user = my_client.pport.users.find_one({"session": session}, {"_id": 1})
    if user is not None:
        data = my_client.pport.history.find_one({"user_id": user["_id"]}, {"user_id": 0, "_id": 0})

        my_client.close()
        return Response(data, status=status.HTTP_200_OK)

    my_client.close()
    return Response({"error": "Invalid session."}, status=status.HTTP_401_UNAUTHORIZED)