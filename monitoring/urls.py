from django.urls import path
from . import views
app_name='monitoring'
urlpatterns=[path('',views.index,name='index'),path('devices/<int:pk>/',views.device_detail,name='detail')]
