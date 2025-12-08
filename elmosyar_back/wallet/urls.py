from django.urls import path
from . import views

urlpatterns = [
    path('mywallet/', views.get_wallet, name='user_wallet'),
    path('deposit/', views.deposit, name='wallet-deposit'),
    path('withdraw/', views.withdraw, name='wallet-withdraw'),
    path('transfer/', views.transfer, name='wallet-transfer'),
    path('purchase/<int:post_id>/', views.purchase, name='post_purchase'),
]