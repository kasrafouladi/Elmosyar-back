from django.contrib import admin
from .models import UserWallet, Transaction

admin.site.register(UserWallet)
admin.site.register(Transaction)
