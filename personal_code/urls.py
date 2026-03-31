"""personal_code URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from registration import views


# app_name = 'retreat'
handler404 = 'registration.views.not_found'
handler500 = 'registration.views.error'

urlpatterns = [
    # url('', include('django.contrib.auth.urls')),
    path(r'accounts/login/', views.log_in),
    path(r'admin/', admin.site.urls),
    path(r'', views.home),
    path(r'home', views.home),
    path(r'registration', views.register),
    path(r'check_who_paid', views.check_who_paid),
    path(r'fellowship', views.fellowship),
    path(r'photos', views.photos),
    path(r'info', views.info),
    path(r'register', views.reg),
    path(r'schedule', views.schedule),
    path(r'full', views.full),
    path(r'paypal_issues', views.paypal_issues),
    path(r'return', views.return_url, name='your-return-view'),
    path(r'cancel', views.canceled_url, name='your-cancel-view'),
    path(r'V4LrfBrC9UbZYm3k/', include('paypal.standard.ipn.urls')),
    path(r'login', views.log_in, name='login'),
    path(r'logout', views.camper_logout),
    path(r'camper_info/', views.camper_info),
    path(r'camper_info/2025_summer_camper_info/', views.camper_info, kwargs=dict(camper_2025_info_summer=True)),
    path(r'camper_info/2024_summer_camper_info/', views.camper_info, kwargs=dict(camper_2024_info_summer=True)),
    path(r'camper_info/2023_summer_camper_info/', views.camper_info, kwargs=dict(camper_2023_info_summer=True)),
    path(r'camper_info/2022_summer_camper_info/', views.camper_info, kwargs=dict(camper_2022_info_summer=True)),
    path(r'camper_info/2021_fall_camper_info/', views.camper_info, kwargs=dict(camper_2021_info_fall=True)),
    path(r'camper_info/2020_camper_info_fall/',views.camper_info, kwargs=dict(camper_2020_info_fall=True)),
    path(r'camper_info/2020_spring_camper_info/', views.camper_info, kwargs=dict(camper_info_2020_spring=True)),
    path(r'camper_info/2019_camper_info_spring/', views.camper_info, kwargs=dict(camper_2019_info_spring=True)),

    path(r'open_reg', views.open_reg),
    path(r'close_reg', views.close_reg),

]
