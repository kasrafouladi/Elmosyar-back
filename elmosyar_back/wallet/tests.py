from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import UserWallet, Transaction, WalletService, InsufficientBalance, WalletError


User = get_user_model()

class WalletServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="ali", password="1234")
        self.wallet = UserWallet.objects.create(user=self.user, balance=100)

    def test_deposit(self):
        WalletService.deposit(self.user, 50)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 150)

    def test_withdraw_success(self):
        WalletService.withdraw(self.user, 70)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 30)

    def test_withdraw_insufficient_balance(self):
        with self.assertRaises(InsufficientBalance):
            WalletService.withdraw(self.user, 500)
