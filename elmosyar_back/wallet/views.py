from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from posts.models import Post, PostMedia
from django.conf import settings

from .models import UserWallet, Transaction, WalletService, WalletError, InsufficientBalance
from .serializer import UserWalletSerializer, TransactionSerializer

# جایگزین کردن لاگر قدیمی
from log_manager.log_config import log_info, log_error, log_warning, log_audit

User = settings.AUTH_USER_MODEL

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet(request):
    try:
        wallet = UserWallet.objects.get(user=request.user)
    except UserWallet.DoesNotExist:
        log_warning(f"Wallet not found for user {request.user.username}", request)
        return Response({"error": True,
                         "message": "کیف پول یافت نشد",
                         "code": "USER_WALLET_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        
    log_info(f"User viewed wallet", request, {
        'balance': wallet.balance,
        'wallet_id': wallet.id
    })
    
    serializer = UserWalletSerializer(wallet)
    return Response({"error": False,
                    "message": "کیف پول با موفقیت دریافت شد",
                    "code": "USER_WALLET_FETCHED",
                    "data": serializer.data}, status=status.HTTP_200_OK)


def wallet_service_handler(service, *args, **kwargs):
    """Handler for wallet services with logging"""
    request = args[0] if len(args) > 0 and hasattr(args[0], 'user') else None
    user = request.user if request else None
    
    try :
        message, code, data = service(*args, **kwargs)
        
        # Log successful operation
        if 'deposit' in str(service):
            log_audit(f"Wallet deposit successful", request, {
                'amount': kwargs.get('amount') if 'amount' in kwargs else args[1],
                'new_balance': data.get('balance') if data else None
            })
        elif 'withdraw' in str(service):
            log_audit(f"Wallet withdrawal successful", request, {
                'amount': kwargs.get('amount') if 'amount' in kwargs else args[1],
                'new_balance': data.get('balance') if data else None
            })
        elif 'purchase_or_transfer' in str(service):
            log_audit(f"Wallet transfer/purchase successful", request, {
                'amount': kwargs.get('amount') if 'amount' in kwargs else args[2],
                'to_user': args[1].username if len(args) > 1 else None,
                'new_balance': data.get('balance') if data else None
            })
        
        return Response({"error": False,
                         "message": message,
                         "code": code,
                         "data": data}, status=status.HTTP_200_OK)
        
    except InsufficientBalance as e:
        log_warning(f"Insufficient balance for wallet operation", request, {
            'service': str(service).split()[1],
            'error': str(e)
        })
        return Response({"error": True,
                         "message": str(e),
                         "code": "INSUFFICIENT_BALANCE"}, status=status.HTTP_409_CONFLICT)
        
    except WalletError as e:
        log_error(f"Wallet error: {str(e)}", request, {
            'service': str(service).split()[1]
        })
        return Response({"error": True,
                         "message": str(e),
                         "code": "SERVER_ERROR"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ValueError as e:
        log_warning(f"Invalid amount for wallet operation: {str(e)}", request, {
            'service': str(service).split()[1]
        })
        return Response({"error": True,
                         "message": "مقدار وارد شده نامعتبر است",
                         "code": "WALLET_INVALID_AMOUNT"}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        log_error(f"Unexpected wallet error: {str(e)}", request, {
            'service': str(service).split()[1]
        })
        return Response({"error": True,
                         "message": "خطای غیر منتظره ای رخ داده",
                         "code": "UNEXPECTED_ERROR"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit(request):
    """Deposit money to wallet"""
    amount = request.data.get("amount")
    log_info(f"Wallet deposit request: {amount}", request)
    return wallet_service_handler(WalletService.deposit, request.user, amount)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw(request):
    """Withdraw money from wallet"""
    amount = request.data.get("amount")
    log_info(f"Wallet withdrawal request: {amount}", request)
    return wallet_service_handler(WalletService.withdraw, request.user, amount)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer(request):
    """Transfer money to another user"""
    to_user_id = request.data.get("to_user_id")
    amount = request.data.get("amount")
    
    log_info(f"Wallet transfer request: {amount} to user {to_user_id}", request)
    
    try :
        to_user = User.objects.get(pk=to_user_id)
    except User.DoesNotExist:
        log_warning(f"Transfer to non-existent user: {to_user_id}", request)
        return Response({"error": True,
                         "message": "کاربر وارد شده یافت نشد",
                         "code": "USER_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        
    return wallet_service_handler(WalletService.purchase_or_transfer, request.user, to_user, amount)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_transactions(request):
    """Get user's transaction history"""
    try:
        wallet = UserWallet.objects.get(user=request.user)
    except UserWallet.DoesNotExist:
        log_warning(f"Transactions requested for non-existent wallet", request)
        return Response({"error": True,
                         "message": "کیف پول یافت نشد",
                         "code": "USER_WALLET_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-registered_in')
    if not transactions.exists():
        log_info(f"No transactions found for user", request)
        return Response({"error": True,
                         "message": "تراکنشی وجود ندارد",
                         "code": "USER_TRANSACTION_NOT_EXIST"}, status=status.HTTP_200_OK)
    
    log_info(f"User viewed transactions history ({transactions.count()} transactions)", request)
    
    serializer = TransactionSerializer(transactions, many=True)
    return Response({"error": False,
                     "message": "تراکنش های کاربر یافت شد",
                     "code": "USER_TRANSACTION_FETCHED",
                     "data": serializer.data}, status=status.HTTP_200_OK)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase(request, post_id):
    """Purchase a post/item"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        log_warning(f"Purchase attempt for non-existent post: {post_id}", request)
        return Response({"error": True,
                         "message": "پست مورد نظر یافت نشد",
                         "code": "POST_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        
    if post.author.id == request.user.id:
        log_warning(f"User attempted to purchase their own post", request, {'post_id': post_id})
        return Response({"error": True,
                         "message": "امکان خرید توسط فروشنده وجود ندارد",
                         "code": "POST_PURCHASE_NOT_ALLOWED"}, status=status.HTTP_409_CONFLICT)
        
    if post.attributes.get('isSoldOut') == True:
        log_warning(f"Purchase attempt for sold out post", request, {'post_id': post_id})
        return Response({"error": True,
                         "message": "این آیتم قبلا به فروش رفته است",
                         "code": "POST_SOLD"}, status=status.HTTP_410_GONE)
        
    price = post.attributes.get('price')
    if price is None:
        log_warning(f"Purchase attempt for post without price", request, {'post_id': post_id})
        return Response({"error": True,
                         "message": "قیمت یافت نشد",
                         "code": "POST_PRICE_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)

    price = int(price)
    
    log_info(f"Purchase request for post {post_id} at price {price}", request, {
        'post_author': post.author.username,
        'price': price
    })
    
    response = wallet_service_handler(
        WalletService.purchase_or_transfer,
        request.user,
        post.author,
        price,
        True
    )

    if response.status_code == 200:
        attrs = post.attributes.copy()
        attrs["isSoldOut"] = True

        post.attributes = attrs
        post.save(update_fields=["attributes"])
        
        log_audit(f"Post purchased successfully", request, {
            'post_id': post_id,
            'price': price,
            'seller': post.author.username
        })

    return response