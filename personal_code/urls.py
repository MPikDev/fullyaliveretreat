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
from django.conf.urls import url, include
from django.contrib import admin
from registration import views


# app_name = 'retreat'
handler404 = 'registration.views.not_found'
handler500 = 'registration.views.error'

urlpatterns = [
    # url('^', include('django.contrib.auth.urls')),
    url(r'^accounts/login/$', views.log_in),
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home2),
    url(r'^home', views.home2),
    url(r'^registration', views.register),
    url(r'^fellowship', views.fellowship),
    url(r'^nature', views.nature),
    url(r'^activities', views.activities),
    # url(r'^info', views.info),
    url(r'^hamburger', views.hamburger),
    url(r'^photos', views.photos),
    url(r'^infotwo', views.info_two),
    url(r'^register', views.reg),
    url(r'^mobile', views.mobile),
    url(r'^schedule', views.schedule),
    url(r'^full', views.full),
    url(r'^return', views.return_url, name='your-return-view'),
    url(r'^cancel', views.canceled_url, name='your-cancel-view'),
    url(r'^REMOVED/', include('paypal.standard.ipn.urls')),
    url(r'^login', views.log_in, name='login'),
    url(r'^logout', views.camper_logout),
    url(r'^camper_info', views.camper_info, name='camper_info'),

]
