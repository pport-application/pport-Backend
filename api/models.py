from django.db import models
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token

# Create your models here.
class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True, 'required': True }}

    def create(self, validated_data): # using predefined create_user function for password encryption
        user = User.objects.create_user(**validated_data)
        Token.objects.create(user=user) # create token immediately (can be returned)
        return user