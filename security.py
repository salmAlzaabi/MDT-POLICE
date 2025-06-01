from functools import wraps
from flask import session, jsonify, request
import re
import secrets
from datetime import datetime, timedelta

# دالة للتحقق من الصلاحيات
def requires_auth(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # التحقق من وجود جلسة نشطة
            if 'user_id' not in session:
                return jsonify({'message': 'غير مصرح به، يرجى تسجيل الدخول'}), 401
            
            # التحقق من الصلاحيات إذا تم تحديدها
            if roles and session.get('role') not in roles:
                return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه الصفحة'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# دالة للتحقق من قوة كلمة المرور
def is_strong_password(password):
    # يجب أن تكون كلمة المرور 8 أحرف على الأقل وتحتوي على حرف كبير وحرف صغير ورقم ورمز خاص
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Z]', password):
        return False
        
    if not re.search(r'[a-z]', password):
        return False
        
    if not re.search(r'[0-9]', password):
        return False
        
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
        
    return True

# دالة لتنظيف المدخلات من الرموز الخاصة
def sanitize_input(input_str):
    if not input_str:
        return input_str
    
    # إزالة أي رموز HTML أو JavaScript
    sanitized = re.sub(r'<[^>]*>', '', input_str)
    
    # إزالة أي أكواد JavaScript
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized

# دالة لتسجيل الأحداث الأمنية
def log_security_event(event_type, user_id=None, details=None):
    # في الإصدار النهائي، يمكن تخزين هذه السجلات في قاعدة البيانات
    # لكن هنا سنكتفي بطباعتها في السجلات
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip_address = request.remote_addr
    
    log_entry = f"[{timestamp}] [{event_type}] IP: {ip_address}, User: {user_id}, Details: {details}"
    print(log_entry)
    
    # يمكن إضافة كود لتخزين السجلات في ملف أو قاعدة بيانات هنا
    
# دالة لإنشاء رمز تحقق من خطوتين
def generate_2fa_code():
    # إنشاء رمز عشوائي من 6 أرقام
    return str(secrets.randbelow(900000) + 100000)

# دالة للتحقق من صلاحية الجلسة
def validate_session():
    # التحقق من وجود جلسة نشطة
    if 'user_id' not in session:
        return False
    
    # التحقق من وقت إنشاء الجلسة
    if 'created_at' not in session:
        # إذا لم يكن هناك وقت إنشاء، قم بتعيينه الآن
        session['created_at'] = datetime.now().timestamp()
        return True
    
    # التحقق من انتهاء صلاحية الجلسة (12 ساعة)
    created_at = datetime.fromtimestamp(session['created_at'])
    if datetime.now() - created_at > timedelta(hours=12):
        # انتهت صلاحية الجلسة
        return False
    
    return True

# دالة لتشفير البيانات الحساسة
def encrypt_sensitive_data(data):
    # في الإصدار النهائي، يمكن استخدام مكتبة تشفير مثل cryptography
    # لكن هنا سنكتفي بتمثيل العملية
    return f"encrypted_{data}"

# دالة لفك تشفير البيانات الحساسة
def decrypt_sensitive_data(encrypted_data):
    # في الإصدار النهائي، يمكن استخدام مكتبة تشفير مثل cryptography
    # لكن هنا سنكتفي بتمثيل العملية
    if encrypted_data.startswith("encrypted_"):
        return encrypted_data[10:]
    return encrypted_data
