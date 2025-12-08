from rest_framework import serializers
from .models import UserWallet, Transaction


class UserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWallet
        fields = ['user', 'balance',]
        

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['wallet', 'amount', 'status', 'type', 'from_user', 'to_user', 'registered_in']
