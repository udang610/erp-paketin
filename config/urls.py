"""
URL configuration for erp_paketin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.i18n import set_language

def index_redirect(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    # Default redirect based on role
    if request.user.roles.filter(can_access_crm=True).exists():
        # Will change to CRM dashboard later
        return redirect('/admin/')
    return redirect('/admin/')

from apps.core.views import dashboard, universal_search, command_palette
from rest_framework import serializers
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField(required=False, write_only=True)
        self.fields['email'] = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        User = get_user_model()
        email = attrs.get('email')
        
        # If email was provided but no username, look up the username
        if email and not attrs.get('username'):
            user = User.objects.filter(email=email).first()
            if user:
                attrs['username'] = user.username
            else:
                attrs['username'] = email

        username = attrs.get('username')
        
        # If username is actually an email, look it up too
        if username and '@' in username:
            user = User.objects.filter(email=username).first()
            if user:
                attrs['username'] = user.username
                
        # If we still don't have a username, validation will fail in super().validate
        if not attrs.get('username'):
            raise serializers.ValidationError('Must include "username" or "email" and "password".')

        return super().validate(attrs)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    # HR Modules (Phase 2 & 3)
    path('hr/attendance/', include('apps.hr.attendance.urls')),
    path('hr/leave/', include('apps.hr.leave.urls')),
    path('hr/payroll/', include('apps.hr.payroll.urls')),
    path('hr/asset_request/', include('apps.hr.asset_request.urls')),
    path('hr/documents/', include('apps.hr.documents.urls')),
    path('audit/', include('apps.audit.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('', dashboard, name='dashboard'),
    path('search/', universal_search, name='universal_search'),
    path('api/search/', command_palette, name='command_palette'),
    path('i18n/setlang/', set_language, name='set_language'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('employees/', include('apps.employees.urls')),
    path('organizations/', include('apps.organizations.urls')),
    path('crm/', include('apps.crm.urls')),
    path('finance/', include('apps.finance.urls')),
    path('operations/', include('apps.operations.urls')),
    path('master/', include('apps.master.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
