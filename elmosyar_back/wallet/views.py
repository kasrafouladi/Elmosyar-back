from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import UserWallet, Transaction, WalletService, WalletError, InsufficientBalance
from .serializer import UserWalletSerializer, TransactionSerializer
from rest_framework import status
from posts.models import Post, PostMedia

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet(request):
    try:
        wallet = UserWallet.objects.get(user=request.user)
    except UserWallet.DoesNotExist:
        return Response({"error": True,
                         "message": "کیف پول یافت نشد",
                         "code": "USER_WALLET_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        
    serializer = UserWalletSerializer(wallet)
    return Response({"error": False,
                    "message": "کیف پول با موفقیت دریافت شد",
                    "code": "USER_WALLET_FETCHED",
                    "data": serializer.data}, status=status.HTTP_200_OK)


def wallet_service_handler(service, *args, **kwargs):
    try :
        message, code, data = service(*args, **kwargs)
        return Response({"error": False,
                         "message": message,
                         "code": code,
                         "data": data}, status=status.HTTP_200_OK)
        
    except InsufficientBalance as e:
        return Response({"error": True,
                         "message": str(e),
                         "code": "INSUFFICIENT_BALANCE"}, status=status.HTTP_409_CONFLICT)
        
    except WalletError as e:
        return Response({"error": True,
                         "message": str(e),
                         "code": "SERVER_ERROR"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ValueError as e:
        return Response({"error": True,
                         "message": "مقدار وارد شده نامعتبر است",
                         "code": "WALLET_INVALID_AMOUNT"}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({"error": True,
                         "message": "خطای غیر منتظره ای رخ داده",
                         "code": "UNEXPECTED_ERROR"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit(request):
    amount = request.data.get("amount")
    return wallet_service_handler(WalletService.deposit, request.user, amount)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw(request):
    amount = request.data.get("amount")
    return wallet_service_handler(WalletService.withdraw, request.user, amount)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer(request):
    to_user_id = request.data.get("to_user_id")
    amount = request.data.get("amount")
    
    try :
        to_user = User.objects.get(pk=to_user_id)
    except User.DoesNotExists:
        return Response({"error": True,
                         "message": "کاربر وارد شده یافت نشد",
                         "code": "USER_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        
    return wallet_service_handler(WalletService.purchase_or_transfer, request.user, to_user, amount)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_transactions(request):
    try:
        wallet = UserWallet.objects.get(user=request.user)
    except UserWallet.DoesNotExist:
        return Response({"error": True,
                         "message": "کیف پول یافت نشد",
                         "code": "USER_WALLET_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-registered_in')
    if not transactions.exists():
        return Response({"error": True,
                         "message": "تراکنشی وجود ندارد",
                         "code": "USER_TRANSACTION_NOT_EXIST"}, status=status.HTTP_200_OK)
    
    serializer = TransactionSerializer(transactions, many=True)
    return Response({"error": False,
                     "message": "تراکنش های کاربر یافت شد",
                     "code": "USER_TRANSACTION_FETCHED",
                     "data": serializer.data}, status=status.HTTP_200_OK)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase(request, post_id):

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": True,
                         "message": "پست مورد نظر یافت نشد",
                         "code": "POST_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)
        
    if post.author.id == request.user.id:
        return Response({"error": True,
                         "message": "امکان خرید توسط فروشنده وجود ندارد",
                         "code": "POST_PURCHASE_NOT_ALLOWED"}, status=status.HTTP_409_CONFLICT)
        
    if post.attributes.get('is_sold'):
        return Response({"error": True,
                         "message": "این آیتم قبلا به فروش رفته است",
                         "code": "POST_SOLD"}, status=status.HTTP_410_GONE)
        
    price = post.attributes.get('price')
    if price is None:
        return Response({"error": True,
                         "message": "قیمت یافت نشد",
                         "code": "POST_PRICE_NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)

    price = int(price)
    
    response = wallet_service_handler(
        WalletService.purchase_or_transfer,
        request.user,
        post.author,
        price,
        True
    )

    if response.status_code == 200:
        attrs = post.attributes.copy()
        attrs["is_sold"] = True

        post.attributes = attrs
        post.save(update_fields=["attributes"])

    return response