from django.urls import path

from .v1 import auth

urlpatterns = [
    path('v1/auth/sign_in/', auth.sign_in),
]