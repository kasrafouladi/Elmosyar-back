from django.db import models
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class UserWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.IntegerField(blank=False, null=False, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s wallet"
    
    
    

class Transaction(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ]
    
    TYPE = [
        ('withdraw', 'Withdraw'),
        ('deposit', 'Diposit'),
        ('payment', 'Payment'),
        ('recieve', 'Recieve'),
        ('refund', 'Refund')
    ]
    
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField(blank=False, null=False)
    registered_in = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    type = models.CharField(max_length=10, choices=TYPE)
    from_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='paid_transactions')
    to_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='recieved_transactions')
    

class WalletError(Exception):
    pass

class InsufficientBalance(Exception):
    pass

class WalletService:

    @staticmethod
    @transaction.atomic
    def deposit(user, amount):
        try:
            wallet = UserWallet.objects.select_for_update().get(user=user)
            wallet.balance += amount
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type="deposite",
                status="success",
                from_user=user
            )
            
            return f"مبلغ {amount} به با موفقیت کیف پول شما اضافه شد", "DEPOSIT_SUCCESS", {"balance" : wallet.balance}
        
        except Exception as e:
            raise WalletError("مشکلی پیش آمده لطفا دوباره سعی کنید") from e
        
    
    
    @staticmethod
    @transaction.atomic
    def withdraw(user, amount):
        try:
            wallet = UserWallet.objects.select_for_update().get(user=user)

            if wallet.balance < amount:
                raise InsufficientBalance("موجودی کافی نمیباشد")

            wallet.balance -= amount
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type="withdraw",
                status="success",
                from_user=user
            )

            return f"مبلغ {amount} با موفقیت از کیف پول شما کسر شد", "WITHDRAW_SUCCESS", {"balance" : wallet.balance}

        except InsufficientBalance:
            raise
        except Exception as e:
            raise WalletError("مشکلی پیش آمده لطفا دوباره سعی کنید") from e
        

    
    
    @staticmethod
    @transaction.atomic
    def purchase_or_transfer(from_user, to_user, amount, is_purchase=False):
        try:
            wallets = (UserWallet.objects.select_for_update().filter(user_id__in=sorted([from_user, to_user])))
            sender_wallet = next(w for w in wallets if w.user_id == from_user.id)
            receiver_wallet = next(w for w in wallets if w.user_id != from_user.id)

            if sender_wallet.balance < amount:
                raise InsufficientBalance("موجودی کافی نمیباشد")

            sender_wallet.balance -= amount
            receiver_wallet.balance += amount

            sender_wallet.save()
            receiver_wallet.save()

            Transaction.objects.create(
                wallet=sender_wallet,
                amount=amount,
                type="payment",
                status="success",
                from_user=from_user,
                to_user=to_user
            )

            Transaction.objects.create(
                wallet=receiver_wallet,
                amount=amount,
                type="recieve",
                status="success",
                from_user=from_user,
                to_user=to_user
            )
            if is_purchase:
                return f"خرید با موفقیت انجام شد", "PURCHASE_SUCCESS", {"balance" : sender_wallet.balance}
            
            return f"مبلغ {amount} با موفقیت منتقل شد", "TRANSFER_SUCCESS", {"balance" : sender_wallet.balance}
        
        except InsufficientBalance:
            raise
        except Exception as e:
            raise WalletError("مشکلی پیش آمده لطفا دوباره سعی کنید") from e