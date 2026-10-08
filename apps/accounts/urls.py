from django.urls import path
from django.contrib.auth import views as auth_views

app_name = 'accounts'

from apps.accounts.views import (
    api_me, user_list, user_create, user_update,
    user_delete, user_reset_password, api_roles,
)

from apps.core.security import CustomLoginView, CustomLogoutView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('api/me/', api_me, name='api_me'),
    path('api/roles/', api_roles, name='api_roles'),
    path('users/', user_list, name='user_list'),
    path('users/create/', user_create, name='user_create'),
    path('users/<uuid:user_id>/edit/', user_update, name='user_update'),
    path('users/<uuid:user_id>/delete/', user_delete, name='user_delete'),
    path('users/<uuid:user_id>/reset-password/', user_reset_password, name='user_reset_password'),
]
