from django.contrib import admin
from django.urls import path
from . import views as mainView
from admins import views as admins
from users import views as usr
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", mainView.index, name="index"),
    path("index/", mainView.index, name="index"),
    path("UserLogin/", mainView.UserLogin, name="UserLogin"),
    path("UserRegisterForm/", mainView.UserRegister, name="UserRegisterForm"),

    # Admin views
    path("AdminHome/", admins.AdminHome, name="AdminHome"),
    path('RegisterUsersView/', admins.RegisterUsersView, name='RegisterUsersView'),
    path('ActivaUsers/', admins.ActivaUsers, name='ActivaUsers'),
    path('DeactivateUsers/', admins.DeactivateUsers, name='DeactivateUsers'),
    path('DeleteUsers/', admins.DeleteUsers, name='DeleteUsers'),
    path('EditUser/', admins.EditUser, name='EditUser'),

  

    # User Views
    path("UserRegisterActions/", usr.UserRegisterActions, name="UserRegisterActions"),
    path("UserHome/", usr.UserHome, name="UserHome"),
    
    path("prediction/", usr.upload_image_prediction, name="prediction"),
    path("live_prediction/", usr.live_prediction, name="live_prediction"),
    path("capture_prediction/", usr.capture_prediction, name="capture_prediction"),
    path("UserHistory/", usr.history, name="UserHistory"),
    path("DeletePrediction/<int:id>/", usr.DeletePrediction, name="DeletePrediction"),
    path("UserLogout/", usr.UserLogout, name="UserLogout"),
    # Forgot Password Flow
    path("ForgotPassword/", usr.ForgotPassword, name="ForgotPassword"),
    path("VerifyOTP/",      usr.VerifyOTP,      name="VerifyOTP"),
    path("ResetPassword/",  usr.ResetPassword,  name="ResetPassword"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)