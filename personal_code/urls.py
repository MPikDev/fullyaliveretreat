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
    url(r'^$', views.home),
    url(r'^home', views.home),
    url(r'^registration', views.register),
    url(r'^check_who_paid', views.check_who_paid),
    url(r'^fellowship', views.fellowship),
    url(r'^photos', views.photos),
    url(r'^info', views.info),
    url(r'^register', views.reg),
    url(r'^schedule', views.schedule),
    url(r'^full', views.full),
    url(r'^paypal_issues', views.paypal_issues),
    url(r'^return', views.return_url, name='your-return-view'),
    url(r'^cancel', views.canceled_url, name='your-cancel-view'),
    url(r'^REMOVED/', include('paypal.standard.ipn.urls')),
    url(r'^login', views.log_in, name='login'),
    url(r'^logout', views.camper_logout),
    url(r'^camper_info/$', views.camper_info),
    url(r'^camper_info/2024_summer_camper_info/$', views.camper_info, kwargs=dict(camper_2024_info_summer=True)),
    url(r'^camper_info/2023_summer_camper_info/$', views.camper_info, kwargs=dict(camper_2023_info_summer=True)),
    url(r'^camper_info/2022_summer_camper_info/$', views.camper_info, kwargs=dict(camper_2022_info_summer=True)),
    url(r'^camper_info/2021_fall_camper_info/$', views.camper_info, kwargs=dict(camper_2021_info_fall=True)),
    url(r'^camper_info/2020_camper_info_fall/$',views.camper_info, kwargs=dict(camper_2020_info_fall=True)),
    url(r'^camper_info/2020_spring_camper_info/$', views.camper_info, kwargs=dict(camper_info_2020_spring=True)),
    url(r'^camper_info/2019_camper_info_spring/$', views.camper_info, kwargs=dict(camper_2019_info_spring=True)),

    url(r'^open_reg', views.open_reg),
    url(r'^close_reg', views.close_reg),

]
