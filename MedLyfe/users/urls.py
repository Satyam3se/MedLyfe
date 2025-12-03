from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.signup_choice, name='signup_choice'),
    path('signup/user/', views.user_signup, name='user_signup'),
    path('signup/doctor/', views.doctor_signup, name='doctor_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
