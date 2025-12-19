import os
import json
from datetime import datetime
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from .log_config import log_audit
from .views import (
    _parse_log_line, 
    _highlight_log_line, 
    _human_readable_size
)


class LogFileAdmin:
    """
    کلاس مدیریت لاگ‌ها در پنل ادمین
    این کلاس مدل ندارد و فقط برای نمایش و مدیریت فایل‌های لاگ است
    """
    
    def __init__(self):
        self.log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        os.makedirs(self.log_dir, exist_ok=True)


@method_decorator(staff_member_required, name='dispatch')
class LogAdminView:
    """ویوهای مدیریت لاگ در پنل ادمین"""
    
    @staticmethod
    def get_log_directory():
        log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    
    @staticmethod
    @staff_member_required
    def log_files_list(request):
        """لیست تمام فایل‌های لاگ"""
        log_dir = LogAdminView.get_log_directory()
        
        log_files = []
        for file_name in os.listdir(log_dir):
            if file_name.endswith('.log'):
                file_path = os.path.join(log_dir, file_name)
                stat = os.stat(file_path)
                
                # خواندن چند خط اول
                preview_lines = []
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for _ in range(3):
                            line = f.readline()
                            if line:
                                preview_lines.append(line.strip())
                except Exception as e:
                    preview_lines = [f"خطا در خواندن فایل: {str(e)}"]
                
                log_files.append({
                    'name': file_name,
                    'size': stat.st_size,
                    'size_human': _human_readable_size(stat.st_size),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'preview': preview_lines
                })
        
        # مرتب سازی بر اساس تاریخ تغییر
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        # لاگ کردن دسترسی
        log_audit(
            f"Admin user '{request.user.username}' viewed log files list in admin panel",
            request
        )
        
        context = {
            'title': 'مدیریت فایل‌های لاگ',
            'log_files': log_files,
            'log_dir': log_dir,
            'total_files': len(log_files),
            'total_size': _human_readable_size(sum(f['size'] for f in log_files)),
        }
        
        return render(request, 'admin/log_manager/log_files_list.html', context)
    
    @staticmethod
    @staff_member_required
    def log_viewer(request):
        """نمایش محتوای یک فایل لاگ با فیلترها"""
        log_dir = LogAdminView.get_log_directory()
        
        # پارامترهای فیلتر
        log_file = request.GET.get('file', 'application.log')
        level = request.GET.get('level', '')
        user_filter = request.GET.get('user', '')
        ip_filter = request.GET.get('ip', '')
        search_text = request.GET.get('search', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 100)), 500)
        
        file_path = os.path.join(log_dir, log_file)
        
        if not os.path.exists(file_path):
            context = {
                'title': 'خطا',
                'error': f'فایل لاگ "{log_file}" یافت نشد'
            }
            return render(request, 'admin/log_manager/log_viewer.html', context)
        
        # خواندن و فیلتر لاگ‌ها
        logs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # پارس کردن خط
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
        
        # معکوس کردن (جدیدترین اول)
        logs.reverse()
        
        # صفحه‌بندی
        paginator = Paginator(logs, per_page)
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        # آمار
        level_stats = {}
        for log in logs[:1000]:
            level = log['parsed'].get('level', 'UNKNOWN')
            level_stats[level] = level_stats.get(level, 0) + 1
        
        # لاگ کردن دسترسی
        log_audit(
            f"Admin user '{request.user.username}' viewed logs from '{log_file}' in admin panel",
            request,
            {'filters': request.GET.dict()}
        )
        
        # لیست فایل‌های لاگ برای منوی انتخاب
        available_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        
        context = {
            'title': f'نمایش لاگ: {log_file}',
            'log_file': log_file,
            'available_files': available_files,
            'logs': page_obj,
            'level_stats': level_stats,
            'file_size': _human_readable_size(os.path.getsize(file_path)),
            'total_logs': len(logs),
            
            # فیلترهای فعال
            'filters': {
                'level': level,
                'user': user_filter,
                'ip': ip_filter,
                'search': search_text,
                'date_from': date_from,
                'date_to': date_to,
                'per_page': per_page,
            },
            
            # گزینه‌های فیلتر
            'level_choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        }
        
        return render(request, 'admin/log_manager/log_viewer.html', context)
    
    @staticmethod
    @staff_member_required
    def download_log(request):
        """دانلود فایل لاگ"""
        log_file = request.GET.get('file')
        
        if not log_file or not log_file.endswith('.log'):
            return JsonResponse({'error': 'نام فایل نامعتبر است'}, status=400)
        
        log_dir = LogAdminView.get_log_directory()
        file_path = os.path.join(log_dir, log_file)
        
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'فایل یافت نشد'}, status=404)
        
        # لاگ کردن دانلود
        log_audit(
            f"Admin user '{request.user.username}' downloaded log file '{log_file}' from admin panel",
            request
        )
        
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{log_file}"'
            return response
    
    @staticmethod
    @staff_member_required
    def clear_log(request):
        """پاک کردن یک فایل لاگ"""
        if request.method != 'POST':
            return JsonResponse({'error': 'فقط متد POST مجاز است'}, status=405)
        
        log_file = request.POST.get('file')
        
        if not log_file or not log_file.endswith('.log'):
            return JsonResponse({'error': 'نام فایل نامعتبر است'}, status=400)
        
        log_dir = LogAdminView.get_log_directory()
        file_path = os.path.join(log_dir, log_file)
        
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'فایل یافت نشد'}, status=404)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Log file cleared by {request.user.username} at {datetime.now()}\n")
            
            # لاگ کردن عملیات
            log_audit(
                f"Admin user '{request.user.username}' cleared log file '{log_file}' from admin panel",
                request
            )
            
            return JsonResponse({'success': True, 'message': 'فایل لاگ با موفقیت پاک شد'})
        except Exception as e:
            return JsonResponse({'error': f'خطا در پاک کردن فایل: {str(e)}'}, status=500)
    
    @staticmethod
    @staff_member_required
    def log_statistics(request):
        """آمار و تحلیل لاگ‌ها"""
        log_dir = LogAdminView.get_log_directory()
        
        statistics = {
            'files': [],
            'total_size': 0,
            'level_distribution': {},
            'user_activity': {},
            'hourly_activity': {str(h).zfill(2): 0 for h in range(24)},
            'daily_activity': {},
            'recent_errors': [],
        }
        
        # بررسی فایل‌ها
        for file_name in os.listdir(log_dir):
            if file_name.endswith('.log'):
                file_path = os.path.join(log_dir, file_name)
                stat = os.stat(file_path)
                
                statistics['total_size'] += stat.st_size
                statistics['files'].append({
                    'name': file_name,
                    'size': _human_readable_size(stat.st_size),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                })
        
        # تحلیل application.log
        app_log = os.path.join(log_dir, 'application.log')
        if os.path.exists(app_log):
            with open(app_log, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    entry = _parse_log_line(line)
                    
                    # توزیع سطح
                    level = entry.get('level', 'UNKNOWN')
                    statistics['level_distribution'][level] = \
                        statistics['level_distribution'].get(level, 0) + 1
                    
                    # فعالیت کاربران
                    user = entry.get('user', 'anonymous')
                    statistics['user_activity'][user] = \
                        statistics['user_activity'].get(user, 0) + 1
                    
                    # فعالیت ساعتی
                    timestamp = entry.get('timestamp', '')
                    if timestamp:
                        try:
                            hour = timestamp.split()[1].split(':')[0]
                            statistics['hourly_activity'][hour] = \
                                statistics['hourly_activity'].get(hour, 0) + 1
                            
                            date = timestamp.split()[0]
                            statistics['daily_activity'][date] = \
                                statistics['daily_activity'].get(date, 0) + 1
                        except:
                            pass
                    
                    # خطاهای اخیر
                    if level in ['ERROR', 'CRITICAL']:
                        statistics['recent_errors'].append({
                            'timestamp': timestamp,
                            'level': level,
                            'user': user,
                            'message': entry.get('message', line)[:100]
                        })
        
        # محدود کردن خطاها به 20 مورد اخیر
        statistics['recent_errors'] = statistics['recent_errors'][-20:]
        
        # مرتب سازی کاربران فعال
        statistics['user_activity'] = dict(
            sorted(statistics['user_activity'].items(), 
                   key=lambda x: x[1], reverse=True)[:15]
        )
        
        # لاگ کردن دسترسی
        log_audit(
            f"Admin user '{request.user.username}' viewed log statistics in admin panel",
            request
        )
        
        context = {
            'title': 'آمار و تحلیل لاگ‌ها',
            'statistics': statistics,
            'total_size_human': _human_readable_size(statistics['total_size']),
        }
        
        return render(request, 'admin/log_manager/log_statistics.html', context)


# ثبت URLهای سفارشی در ادمین
class LogManagerAdminSite:
    """کلاس برای اضافه کردن URLهای سفارشی به پنل ادمین"""
    
    def get_urls(self):
        urls = [
            path('logs/', LogAdminView.log_files_list, name='log_files_list'),
            path('logs/viewer/', LogAdminView.log_viewer, name='log_viewer'),
            path('logs/download/', LogAdminView.download_log, name='log_download'),
            path('logs/clear/', LogAdminView.clear_log, name='log_clear'),
            path('logs/statistics/', LogAdminView.log_statistics, name='log_statistics'),
        ]
        return urls


# اضافه کردن لینک به منوی ادمین
def add_log_menu_item(request):
    """اضافه کردن آیتم منو برای لاگ‌ها"""
    if request.user.is_staff:
        return {
            'log_manager_menu': {
                'title': '🔍 مدیریت لاگ‌ها',
                'url': '/admin/logs/',
                'description': 'مشاهده و مدیریت فایل‌های لاگ سیستم'
            }
        }
    return {}


# برای نمایش در لیست اپلیکیشن‌ها
class LogManagerConfig:
    """تنظیمات نمایش در پنل ادمین"""
    name = 'log_manager'
    verbose_name = '🔍 مدیریت لاگ‌ها'
    
    def ready(self):
        # می‌توانید سیگنال‌ها یا تنظیمات دیگر را اینجا اضافه کنید
        pass


# ثبت در ادمین
admin.site.site_header = "پنل مدیریت الموسیار"
admin.site.site_title = "الموسیار"
admin.site.index_title = "خوش آمدید به پنل مدیریت"

# اضافه کردن URLها به ادمین
from django.contrib import admin as django_admin
original_get_urls = django_admin.site.get_urls

def custom_get_urls():
    custom_urls = LogManagerAdminSite().get_urls()
    return custom_urls + original_get_urls()

django_admin.site.get_urls = custom_get_urls
