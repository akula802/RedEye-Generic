# (api) app-level urls.py

# Core library inserts
from django.urls import path #, include

# 3rd-party imports
#from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

# Local app imports
from . import views


#########################


# Create the routers, these allow GET and POST requests
#router = routers.DefaultRouter()
# router.register('lob_servers', views.lob_servers)
#router.register('lob_servers', views.lob_servers, basename='queryset')



# Ok the URLs go here
urlpatterns = [
    #path('api/', include(router.urls)),
    path('lob_servers/', views.lob_servers.as_view(), name='lob_servers'),
    path('get-auth/', obtain_auth_token, name='get-auth'),
]

