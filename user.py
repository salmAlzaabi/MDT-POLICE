from flask import Blueprint, request, jsonify, session
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    # التحقق من الصلاحيات (فقط المدير والقائد يمكنهم عرض جميع المستخدمين)
    if session.get('role') not in ['admin', 'commander']:
        return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه البيانات'}), 403
    
    users = User.query.all()
    return jsonify({'users': [user.to_dict() for user in users]}), 200

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # التحقق من الصلاحيات (المستخدم نفسه أو المدير أو القائد أو الضابط المسؤول)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_user_id != user_id and current_role not in ['admin', 'commander', 'officer']:
        return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه البيانات'}), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'المستخدم غير موجود'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # التحقق من الصلاحيات (المدير فقط أو القائد)
    current_role = session.get('role')
    
    if current_role not in ['admin', 'commander']:
        return jsonify({'message': 'غير مصرح لك بتعديل بيانات المستخدمين'}), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'المستخدم غير موجود'}), 404
    
    data = request.get_json()
    
    # تحديث البيانات المسموح بتعديلها
    allowed_fields = ['full_name', 'rank', 'unit', 'role', 'status']
    
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    # تحديث كلمة المرور إذا تم توفيرها
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث بيانات المستخدم بنجاح',
        'user': user.to_dict()
    }), 200

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # التحقق من الصلاحيات (المدير فقط)
    current_role = session.get('role')
    
    if current_role != 'admin':
        return jsonify({'message': 'غير مصرح لك بحذف المستخدمين'}), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'المستخدم غير موجود'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف المستخدم بنجاح'}), 200
