import logging
import logging.handlers
import os
import json
from datetime import datetime
from django.conf import settings
from django.utils import timezone

class AdvancedLogger:
    """
    سیستم لاگینگ پیشرفته
    """
    
    def __init__(self):
        self.log_dir = self._get_log_directory()
        self.setup_loggers()
    
    def _get_log_directory(self):
        log_dir = getattr(settings, 'LOG_DIR', None)
        if not log_dir:
            base_dir = settings.BASE_DIR
            log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    
    def setup_loggers(self):
        """تنظیم انواع مختلف لاگر"""
        
        # فرمترهای مختلف
        detailed_formatter = logging.Formatter(
            '📅 %(asctime)s | 📊 %(levelname)s | 👤 %(user)s | 🌐 %(ip)s | '
            '📁 %(module)s:%(lineno)d | 📝 %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # لاگر اصلی اپلیکیشن
        self._setup_logger(
            name='app',
            filename='application.log',
            level=logging.DEBUG if settings.DEBUG else logging.INFO,
            formatter=detailed_formatter,
            max_bytes=10 * 1024 * 1024,
            backup_count=10
        )
        
        # لاگر API
        self._setup_logger(
            name='api',
            filename='api_requests.log',
            level=logging.INFO,
            formatter=detailed_formatter,
            max_bytes=5 * 1024 * 1024,
            backup_count=5
        )
        
        # لاگر امنیتی
        self._setup_logger(
            name='security',
            filename='security.log',
            level=logging.WARNING,
            formatter=detailed_formatter,
            max_bytes=2 * 1024 * 1024,
            backup_count=20
        )
        
        # لاگر دیتابیس
        self._setup_logger(
            name='database',
            filename='database.log',
            level=logging.WARNING,
            formatter=detailed_formatter,
            max_bytes=5 * 1024 * 1024,
            backup_count=5
        )
        
        # لاگر عملیات‌های مهم
        self._setup_logger(
            name='audit',
            filename='audit_trail.log',
            level=logging.INFO,
            formatter=detailed_formatter,
            max_bytes=10 * 1024 * 1024,
            backup_count=30
        )
    
    def _setup_logger(self, name, filename, level, formatter, max_bytes, backup_count):
        """تنظیم یک لاگر خاص"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False
        
        if logger.handlers:
            logger.handlers.clear()
        
        file_path = os.path.join(self.log_dir, filename)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        if settings.DEBUG:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    def log(self, logger_name, level, message, request=None, extra_data=None):
        """ثبت لاگ با کانتکست کامل"""
        logger = logging.getLogger(logger_name)
        
        log_context = {
            'user': 'anonymous',
            'ip': 'unknown',
            'timestamp': timezone.now().isoformat()
        }
        
        if request:
            if hasattr(request, 'user') and request.user.is_authenticated:
                log_context['user'] = request.user.username
                log_context['user_id'] = request.user.id
                log_context['is_superuser'] = request.user.is_superuser
            
            if hasattr(request, 'META'):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    log_context['ip'] = x_forwarded_for.split(',')[0]
                else:
                    log_context['ip'] = request.META.get('REMOTE_ADDR', 'unknown')
            
            log_context.update({
                'method': request.method,
                'path': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')
            })
        
        if extra_data:
            if isinstance(extra_data, dict):
                log_context.update(extra_data)
            else:
                log_context['extra'] = str(extra_data)
        
        if isinstance(message, dict):
            message_str = json.dumps(message, ensure_ascii=False)
        else:
            message_str = str(message)
        
        full_message = f"{message_str}"
        
        log_method = {
            'debug': logger.debug,
            'info': logger.info,
            'warning': logger.warning,
            'error': logger.error,
            'critical': logger.critical
        }.get(level.lower(), logger.info)
        
        log_method(full_message, extra=log_context)


# ایجاد نمونه اصلی
logger = AdvancedLogger()

# توابع کمکی برای استفاده سریع
def log_debug(msg, request=None, extra=None):
    logger.log('app', 'debug', msg, request, extra)

def log_info(msg, request=None, extra=None):
    logger.log('app', 'info', msg, request, extra)

def log_warning(msg, request=None, extra=None):
    logger.log('app', 'warning', msg, request, extra)

def log_error(msg, request=None, extra=None):
    logger.log('app', 'error', msg, request, extra)

def log_critical(msg, request=None, extra=None):
    logger.log('app', 'critical', msg, request, extra)

def log_api_request(msg, request=None, extra=None):
    logger.log('api', 'info', msg, request, extra)

def log_security(msg, request=None, extra=None):
    logger.log('security', 'warning', msg, request, extra)

def log_audit(action, request=None, extra=None):
    logger.log('audit', 'info', action, request, extra)