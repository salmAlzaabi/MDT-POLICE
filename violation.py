from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from datetime import datetime

violation_bp = Blueprint('violation', __name__)

class Violation(db.Model):
    __tablename__ = 'violations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    recorder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_taken = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending')  # pending, resolved, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d %H:%M'),
            'recorder_id': self.recorder_id,
            'action_taken': self.action_taken,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M')
        }

@violation_bp.route('/violations', methods=['GET'])
def get_violations():
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    # المدير والقائد يمكنهم رؤية جميع المخالفات
    if current_role in ['admin', 'commander']:
        violations = Violation.query.all()
    # الضابط يمكنه رؤية مخالفات وحدته فقط
    elif current_role == 'officer':
        officer = User.query.get(current_user_id)
        unit_users = User.query.filter_by(unit=officer.unit).all()
        unit_user_ids = [user.id for user in unit_users]
        violations = Violation.query.filter(Violation.user_id.in_(unit_user_ids)).all()
    # الجندي يمكنه رؤية مخالفاته فقط
    else:
        violations = Violation.query.filter_by(user_id=current_user_id).all()
    
    return jsonify({'violations': [violation.to_dict() for violation in violations]}), 200

@violation_bp.route('/violations', methods=['POST'])
def create_violation():
    # التحقق من الصلاحيات (فقط المدير والقائد والضابط يمكنهم تسجيل مخالفات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander', 'officer']:
        return jsonify({'message': 'غير مصرح لك بتسجيل المخالفات'}), 403
    
    data = request.get_json()
    
    # التحقق من وجود البيانات المطلوبة
    required_fields = ['user_id', 'type', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'حقل {field} مطلوب'}), 400
    
    # التحقق من وجود المستخدم المخالف
    user = User.query.get(data.get('user_id'))
    if not user:
        return jsonify({'message': 'المستخدم غير موجود'}), 404
    
    # إذا كان الضابط، يجب أن يكون المستخدم المخالف من نفس الوحدة
    if current_role == 'officer':
        officer = User.query.get(current_user_id)
        if user.unit != officer.unit:
            return jsonify({'message': 'غير مصرح لك بتسجيل مخالفات لعساكر من وحدات أخرى'}), 403
    
    # إنشاء مخالفة جديدة
    new_violation = Violation(
        user_id=data.get('user_id'),
        type=data.get('type'),
        description=data.get('description'),
        recorder_id=current_user_id,
        action_taken=data.get('action_taken', ''),
        status=data.get('status', 'pending')
    )
    
    db.session.add(new_violation)
    db.session.commit()
    
    return jsonify({
        'message': 'تم تسجيل المخالفة بنجاح',
        'violation': new_violation.to_dict()
    }), 201

@violation_bp.route('/violations/<int:violation_id>', methods=['GET'])
def get_violation(violation_id):
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    violation = Violation.query.get(violation_id)
    
    if not violation:
        return jsonify({'message': 'المخالفة غير موجودة'}), 404
    
    # التحقق من صلاحية الوصول للمخالفة
    if current_role in ['admin', 'commander']:
        # المدير والقائد يمكنهم الوصول لجميع المخالفات
        pass
    elif current_role == 'officer':
        # الضابط يمكنه الوصول لمخالفات وحدته فقط
        officer = User.query.get(current_user_id)
        violator = User.query.get(violation.user_id)
        if violator.unit != officer.unit:
            return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه المخالفة'}), 403
    else:
        # الجندي يمكنه الوصول لمخالفاته فقط
        if violation.user_id != current_user_id:
            return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه المخالفة'}), 403
    
    return jsonify({'violation': violation.to_dict()}), 200

@violation_bp.route('/violations/<int:violation_id>', methods=['PUT'])
def update_violation(violation_id):
    # التحقق من الصلاحيات (فقط المدير والقائد والضابط يمكنهم تعديل المخالفات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander', 'officer']:
        return jsonify({'message': 'غير مصرح لك بتعديل المخالفات'}), 403
    
    violation = Violation.query.get(violation_id)
    
    if not violation:
        return jsonify({'message': 'المخالفة غير موجودة'}), 404
    
    # التحقق من صلاحية تعديل المخالفة
    if current_role == 'officer':
        # الضابط يمكنه تعديل مخالفات وحدته فقط
        officer = User.query.get(current_user_id)
        violator = User.query.get(violation.user_id)
        if violator.unit != officer.unit:
            return jsonify({'message': 'غير مصرح لك بتعديل هذه المخالفة'}), 403
    
    data = request.get_json()
    
    # تحديث البيانات المسموح بتعديلها
    allowed_fields = ['type', 'description', 'action_taken', 'status']
    
    for field in allowed_fields:
        if field in data:
            setattr(violation, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث المخالفة بنجاح',
        'violation': violation.to_dict()
    }), 200

@violation_bp.route('/violations/<int:violation_id>', methods=['DELETE'])
def delete_violation(violation_id):
    # التحقق من الصلاحيات (فقط المدير والقائد يمكنهم حذف المخالفات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander']:
        return jsonify({'message': 'غير مصرح لك بحذف المخالفات'}), 403
    
    violation = Violation.query.get(violation_id)
    
    if not violation:
        return jsonify({'message': 'المخالفة غير موجودة'}), 404
    
    db.session.delete(violation)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف المخالفة بنجاح'}), 200
