import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.db.models import Q

from .permissions import IsSuperUser
from .log_config import logger, log_info, log_error

# ════════════════════════════════════════════════════════════
# 📊 Log Management Endpoints (Only for Superusers)
# ════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperUser])
def list_log_files(request):
    """
    لیست فایل‌های لاگ موجود
    فقط برای سوپر یوزرها
    """
    try:
        log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        
        if not os.path.exists(log_dir):
            return Response({
                'success': False,
                'message': 'پوشه لاگ‌ها وجود ندارد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        log_files = []
        for file_name in os.listdir(log_dir):
            if file_name.endswith('.log'):
                file_path = os.path.join(log_dir, file_name)
                stat = os.stat(file_path)
                
                # خواندن چند خط اول برای نمونه
                preview_lines = []
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for _ in range(5):
                            line = f.readline()
                            if line:
                                preview_lines.append(line.strip())
                except:
                    preview_lines = ["قابل خواندن نیست"]
                
                log_files.append({
                    'name': file_name,
                    'size': stat.st_size,
                    'size_human': _human_readable_size(stat.st_size),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'preview': preview_lines[:3]  # فقط ۳ خط اول
                })
        
        # لاگ کردن دسترسی
        logger.audit_trail(
            f"Superuser '{request.user.username}' viewed log files list",
            request
        )
        
        return Response({
            'success': True,
            'log_dir': log_dir,
            'files': sorted(log_files, key=lambda x: x['modified'], reverse=True),
            'total_files': len(log_files)
        })
        
    except Exception as e:
        log_error(f"Failed to list log files: {str(e)}", request)
        return Response({
            'success': False,
            'message': 'خطا در دریافت لیست فایل‌های لاگ'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperUser])
def read_logs(request):
    """
    خواندن لاگ‌ها با فیلتر و صفحه‌بندی
    فقط برای سوپر یوزرها
    """
    try:
        # پارامترهای فیلتر
        log_file = request.GET.get('file', 'application.log')
        level = request.GET.get('level')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        user_filter = request.GET.get('user')
        ip_filter = request.GET.get('ip')
        search_text = request.GET.get('search')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 100)), 1000)
        
        # مسیر فایل لاگ
        log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        file_path = os.path.join(log_dir, log_file)
        
        # بررسی وجود فایل
        if not os.path.exists(file_path):
            return Response({
                'success': False,
                'message': f'فایل لاگ "{log_file}" یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # خواندن و فیلتر لاگ‌ها
        logs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # پارس کردن خط لاگ
                log_entry = _parse_log_line(line)
                
                # اعمال فیلترها
                include = True
                
                if level and log_entry.get('level') != level.upper():
                    include = False
                
                if user_filter and user_filter not in log_entry.get('user', ''):
                    include = False
                
                if ip_filter and ip_filter not in log_entry.get('ip', ''):
                    include = False
                
                if search_text and search_text.lower() not in line.lower():
                    include = False
                
                if date_from and log_entry.get('timestamp'):
                    try:
                        log_date = datetime.strptime(log_entry['timestamp'], '%Y-%m-%d %H:%M:%S')
                        filter_date = datetime.strptime(date_from, '%Y-%m-%d')
                        if log_date.date() < filter_date.date():
                            include = False
                    except:
                        pass
                
                if date_to and log_entry.get('timestamp'):
                    try:
                        log_date = datetime.strptime(log_entry['timestamp'], '%Y-%m-%d %H:%M:%S')
                        filter_date = datetime.strptime(date_to, '%Y-%m-%d')
                        if log_date.date() > filter_date.date():
                            include = False
                    except:
                        pass
                
                if include:
                    logs.append({
                        'raw': line,
                        'parsed': log_entry,
                        'highlight': _highlight_log_line(line)
                    })
        
        # مرتب سازی (جدیدترین اول)
        logs.reverse()
        
        # صفحه‌بندی
        paginator = Paginator(logs, per_page)
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        # آمار
        level_stats = {}
        user_stats = {}
        for log in logs[:1000]:  # فقط ۱۰۰۰ خط اول برای آمار
            entry = log['parsed']
            level = entry.get('level', 'UNKNOWN')
            user = entry.get('user', 'anonymous')
            
            level_stats[level] = level_stats.get(level, 0) + 1
            user_stats[user] = user_stats.get(user, 0) + 1
        
        # لاگ کردن دسترسی
        logger.audit_trail(
            f"Superuser '{request.user.username}' read logs from '{log_file}'",
            request,
            {'filters': request.GET.dict()}
        )
        
        return Response({
            'success': True,
            'file': log_file,
            'logs': [log['highlight'] for log in page_obj.object_list],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'statistics': {
                'levels': level_stats,
                'top_users': dict(sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                'file_size': _human_readable_size(os.path.getsize(file_path))
            }
        })
        
    except Exception as e:
        log_error(f"Failed to read logs: {str(e)}", request)
        return Response({
            'success': False,
            'message': f'خطا در خواندن لاگ‌ها: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperUser])
def download_log_file(request, file_name):
    """
    دانلود کامل یک فایل لاگ
    فقط برای سوپر یوزرها
    """
    try:
        log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        file_path = os.path.join(log_dir, file_name)
        
        # بررسی امنیتی: فقط فایل‌های .log
        if not file_name.endswith('.log'):
            return Response({
                'success': False,
                'message': 'فقط فایل‌های لاگ مجاز هستند'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not os.path.exists(file_path):
            return Response({
                'success': False,
                'message': 'فایل لاگ یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # لاگ کردن دانلود
        logger.audit_trail(
            f"Superuser '{request.user.username}' downloaded log file '{file_name}'",
            request
        )
        
        # ارسال فایل
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
            
    except Exception as e:
        log_error(f"Failed to download log file: {str(e)}", request)
        return Response({
            'success': False,
            'message': 'خطا در دانلود فایل لاگ'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsSuperUser])
def clear_log_file(request, file_name):
    """
    پاک کردن محتوای یک فایل لاگ
    فقط برای سوپر یوزرها
    """
    try:
        log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        file_path = os.path.join(log_dir, file_name)
        
        # بررسی امنیتی
        if not file_name.endswith('.log'):
            return Response({
                'success': False,
                'message': 'فقط فایل‌های لاگ مجاز هستند'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not os.path.exists(file_path):
            return Response({
                'success': False,
                'message': 'فایل لاگ یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # پاک کردن فایل (ایجاد فایل خالی جدید)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Log file cleared by {request.user.username} at {datetime.now()}\n")
        
        # لاگ کردن عملیات
        logger.audit_trail(
            f"Superuser '{request.user.username}' cleared log file '{file_name}'",
            request
        )
        
        return Response({
            'success': True,
            'message': f'فایل "{file_name}" با موفقیت پاک شد'
        })
        
    except Exception as e:
        log_error(f"Failed to clear log file: {str(e)}", request)
        return Response({
            'success': False,
            'message': 'خطا در پاک کردن فایل لاگ'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperUser])
def get_log_statistics(request):
    """
    دریافت آمار و تحلیل لاگ‌ها
    فقط برای سوپر یوزرها
    """
    try:
        log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        
        statistics = {
            'total_files': 0,
            'total_size': 0,
            'files': [],
            'recent_errors': [],
            'top_users': {},
            'activity_by_hour': {}
        }
        
        # بررسی فایل‌های لاگ
        for file_name in os.listdir(log_dir):
            if file_name.endswith('.log'):
                file_path = os.path.join(log_dir, file_name)
                stat = os.stat(file_path)
                
                statistics['total_files'] += 1
                statistics['total_size'] += stat.st_size
                
                statistics['files'].append({
                    'name': file_name,
                    'size': stat.st_size,
                    'size_human': _human_readable_size(stat.st_size),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
        
        # تحلیل فایل application.log برای آمار
        app_log_path = os.path.join(log_dir, 'application.log')
        if os.path.exists(app_log_path):
            errors_today = []
            user_activities = {}
            hourly_activity = {str(h).zfill(2): 0 for h in range(24)}
            
            with open(app_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # استخراج اطلاعات
                    entry = _parse_log_line(line)
                    
                    # شمارش خطاهای امروز
                    if entry.get('level') in ['ERROR', 'CRITICAL']:
                        if 'today' in entry.get('timestamp', ''):
                            errors_today.append(entry)
                    
                    # آمار کاربران
                    user = entry.get('user', 'anonymous')
                    user_activities[user] = user_activities.get(user, 0) + 1
                    
                    # فعالیت ساعتی
                    timestamp = entry.get('timestamp')
                    if timestamp:
                        try:
                            hour = timestamp.split()[1].split(':')[0]
                            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
                        except:
                            pass
            
            statistics['recent_errors'] = errors_today[-10:]  # ۱۰ خطای آخر
            statistics['top_users'] = dict(sorted(
                user_activities.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10])
            statistics['activity_by_hour'] = hourly_activity
        
        # لاگ کردن دسترسی
        logger.audit_trail(
            f"Superuser '{request.user.username}' viewed log statistics",
            request
        )
        
        return Response({
            'success': True,
            'statistics': statistics,
            'total_size_human': _human_readable_size(statistics['total_size'])
        })
        
    except Exception as e:
        log_error(f"Failed to get log statistics: {str(e)}", request)
        return Response({
            'success': False,
            'message': 'خطا در دریافت آمار لاگ‌ها'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_activity_logs(request):
    """
    کاربران معمولی می‌توانند لاگ‌های فعالیت خودشان را ببینند
    """
    try:
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 50)), 200)
        
        log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        app_log_path = os.path.join(log_dir, 'application.log')
        
        if not os.path.exists(app_log_path):
            return Response({
                'success': False,
                'message': 'فایل لاگ یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # فیلتر لاگ‌های کاربر جاری
        user_logs = []
        username = request.user.username
        
        with open(app_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if username in line:
                    user_logs.append({
                        'raw': line,
                        'highlight': _highlight_log_line(line)
                    })
        
        # مرتب سازی معکوس (جدیدترین اول)
        user_logs.reverse()
        
        # صفحه‌بندی
        paginator = Paginator(user_logs, per_page)
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        return Response({
            'success': True,
            'username': username,
            'logs': [log['highlight'] for log in page_obj.object_list],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        
    except Exception as e:
        log_error(f"Failed to get user activity logs: {str(e)}", request)
        return Response({
            'success': False,
            'message': 'خطا در دریافت لاگ‌های فعالیت'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ════════════════════════════════════════════════════════════
# 🛠️ Helper Functions
# ════════════════════════════════════════════════════════════

def _parse_log_line(line):
    """پارس کردن یک خط لاگ به اجزای تشکیل دهنده"""
    try:
        # فرمت: 📅 2024-01-01 12:00:00 | 📊 INFO | 👤 admin | 🌐 127.0.0.1 | 📁 module:42 | 📝 message
        pattern = r'📅 (.+?) \| 📊 (.+?) \| 👤 (.+?) \| 🌐 (.+?) \| 📁 (.+?) \| 📝 (.+)'
        match = re.match(pattern, line)
        
        if match:
            return {
                'timestamp': match.group(1),
                'level': match.group(2),
                'user': match.group(3),
                'ip': match.group(4),
                'location': match.group(5),
                'message': match.group(6)
            }
        
        # فرمت قدیمی‌تر
        patterns = [
            r'\[(.+?)\] \[(.+?)\] \[(.+?)\] \[(.+?):(\d+)\] \[User:(.+?)\] \[IP:(.+?)\] - (.+)',
            r'\[(.+?)\] \[(.+?)\] \[(.+?)\] - (.+)'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                if len(match.groups()) == 8:
                    return {
                        'timestamp': match.group(1),
                        'level': match.group(2),
                        'logger': match.group(3),
                        'module': match.group(4),
                        'line': match.group(5),
                        'user': match.group(6),
                        'ip': match.group(7),
                        'message': match.group(8)
                    }
                elif len(match.groups()) == 4:
                    return {
                        'timestamp': match.group(1),
                        'level': match.group(2),
                        'logger': match.group(3),
                        'message': match.group(4)
                    }
    except:
        pass
    
    # اگر نتوانستیم پارس کنیم
    return {'raw': line}


def _highlight_log_line(line):
    """هایلایت کردن خط لاگ برای نمایش بهتر"""
    # رنگ‌بندی بر اساس سطح
    colors = {
        'DEBUG': '#6c757d',    # خاکستری
        'INFO': '#0d6efd',     # آبی
        'WARNING': '#ffc107',  # زرد
        'ERROR': '#dc3545',    # قرمز
        'CRITICAL': '#6f42c1'  # بنفش
    }
    
    # تشخیص سطح
    level = None
    for lvl in colors:
        if lvl in line:
            level = lvl
            break
    
    # اگر سطح پیدا شد، رنگ‌بندی کن
    if level and level in colors:
        colored_level = f'<span style="color: {colors[level]}; font-weight: bold;">{level}</span>'
        line = line.replace(level, colored_level)
    
    # هایلایت کاربر
    if '👤' in line:
        line = line.replace('👤', '<span style="color: #20c997;">👤</span>')
    
    # هایلایت IP
    if '🌐' in line:
        line = line.replace('🌐', '<span style="color: #fd7e14;">🌐</span>')
    
    return line


def _human_readable_size(size_bytes):
    """تبدیل بایت به فرمت خوانا"""
    if size_bytes == 0:
        return "0B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {units[i]}"