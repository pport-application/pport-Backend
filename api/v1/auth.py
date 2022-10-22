import uuid
from pymongo import MongoClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(['GET', ])
def sign_in(request):
    if request.GET.get("email") is None or request.GET.get("password") is None:
        content = {'error': 'Missing parameters'}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    email = str(request.GET.get("email"))
    password = str(request.GET.get("password"))

    my_client = MongoClient("mongodb+srv://pport:pport123@pport.anzux.mongodb.net/pport?retryWrites=true&w=majority")

    my_database = my_client["pport"]
    my_column = my_database["users"]

    if my_column.find_one({"email": email, "password": password}):
        my_query = {"email": email}
        new_values = {"$set": {"session": str(uuid.uuid1())}}
        my_column.update_one(my_query, new_values)
        item = my_column.find_one({"email": email, "password": password})

        login_response = {'user_id': str(item.get('_id')),
                          'session': item.get('session'),
                          'name': item.get('name'),
                          'surname': item.get('surname'),
                          'watchlist': item.get('watchlist')}
        my_client.close()
        return Response(login_response, status=status.HTTP_200_OK)

    my_client.close()

    return Response({'error': 'Invalid username or password'}, status=status.HTTP_404_NOT_FOUND)
