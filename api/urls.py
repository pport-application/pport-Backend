from django.urls import path

from .v1 import auth

urlpatterns = [
    path('v1/auth/sign_in/', auth.sign_in),
    path('v1/auth/sign_out/', auth.sign_out),
    path('v1/auth/reset_password', auth.reset_password),
    path('v1/auth/sign_up', auth.sign_up),
    path('v1/auth/validate_reset_code', auth.validate_reset_code),
    path('v1/auth/change_password', auth.change_password),
]