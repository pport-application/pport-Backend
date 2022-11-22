from django.urls import path

from .v1 import auth, user, admin, watchlist, finance, portfolio

urlpatterns = [
    path("v1/auth/sign_in", auth.sign_in),
    path("v1/auth/sign_out", auth.sign_out),
    path("v1/auth/reset_password", auth.reset_password),
    path("v1/auth/sign_up", auth.sign_up),
    path("v1/auth/validate_reset_code", auth.validate_reset_code),
    path("v1/auth/change_password", auth.change_password),
    path("v1/auth/validate_session", auth.validate_session),
    path("v1/auth/get_token", auth.get_token),
    path("v1/admin/delete_reset_codes", admin.delete_reset_codes),
    path("v1/admin/update_database", admin.update_database),
    path("v1/admin/update_mongo", admin.update_mongo),
    path("v1/user/delete_user", user.delete_user),
    path("v1/user/get_user_info", user.get_user_info),
    path("v1/user/update_user_info", user.update_user_info),
    path("v1/user/change_password", user.change_password),
    path("v1/watchlist/get_watchlist_data", watchlist.get_watchlist_data),
    path("v1/watchlist/delete_watchlist_item", watchlist.delete_watchlist_item),
    path("v1/watchlist/add_watchlist_item", watchlist.add_watchlist_item),
    path("v1/finance/get_tickers", finance.get_tickers),
    path("v1/finance/get_exchange_codes", finance.get_exchange_codes),
    path("v1/finance/get_currency_codes", finance.get_currency_codes),
    path("v1/portfolio/deposit_currency", portfolio.deposit_currency),
    path("v1/portfolio/withdraw_currency", portfolio.withdraw_currency),
    path("v1/portfolio/get_portfolio", portfolio.get_portfolio),
    path("v1/portfolio/deposit_ticker", portfolio.deposit_ticker),
    path("v1/portfolio/withdraw_ticker", portfolio.withdraw_ticker),
    path("v1/portfolio/get_history", portfolio.get_history),
    path("v1/portfolio/delete_history", portfolio.delete_history),
]