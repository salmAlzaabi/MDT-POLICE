from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, db
import secrets
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'يرجى توفير اسم المستخدم وكلمة المرور'}), 400
    
    user = User.query.filter_by(username=data.get('username')).first()
    
    if not user or not user.check_password(data.get('password')):
        return jsonify({'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
    
    if user.status != 'active':
        return jsonify({'message': 'الحساب غير نشط، يرجى التواصل مع المسؤول'}), 403
    
    session['user_id'] = user.id
    session['role'] = user.role
    
    return jsonify({
        'message': 'تم تسجيل الدخول بنجاح',
        'user': user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return jsonify({'message': 'تم تسجيل الخروج بنجاح'}), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # التحقق من وجود البيانات المطلوبة
    required_fields = ['full_name', 'username', 'email', 'password', 'rank', 'unit', 'military_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'حقل {field} مطلوب'}), 400
    
    # التحقق من عدم وجود مستخدم بنفس اسم المستخدم أو البريد الإلكتروني أو الرقم العسكري
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'message': 'اسم المستخدم موجود بالفعل'}), 400
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'message': 'البريد الإلكتروني موجود بالفعل'}), 400
    
    if User.query.filter_by(military_id=data.get('military_id')).first():
        return jsonify({'message': 'الرقم العسكري موجود بالفعل'}), 400
    
    # إنشاء مستخدم جديد
    new_user = User(
        full_name=data.get('full_name'),
        username=data.get('username'),
        email=data.get('email'),
        rank=data.get('rank'),
        unit=data.get('unit'),
        military_id=data.get('military_id'),
        role=data.get('role', 'soldier'),  # افتراضي: جندي
        status='active'
    )
    
    new_user.set_password(data.get('password'))
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'تم إنشاء الحساب بنجاح',
        'user': new_user.to_dict()
    }), 201

@auth_bp.route('/user', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    user = User.query.get(user_id)
    
    if not user:
        session.pop('user_id', None)
        session.pop('role', None)
        return jsonify({'message': 'المستخدم غير موجود'}), 404
    
    return jsonify({'user': user.to_dict()}), 200
