from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from datetime import datetime

shift_bp = Blueprint('shift', __name__)

class Shift(db.Model):
    __tablename__ = 'shifts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # guard, patrol, office, etc.
    status = db.Column(db.String(50), default='scheduled')  # scheduled, in-progress, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'start_date': self.start_date.strftime('%Y-%m-%d %H:%M'),
            'end_date': self.end_date.strftime('%Y-%m-%d %H:%M'),
            'location': self.location,
            'type': self.type,
            'status': self.status
        }

@shift_bp.route('/shifts', methods=['GET'])
def get_shifts():
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    # المدير والقائد يمكنهم رؤية جميع المناوبات
    if current_role in ['admin', 'commander']:
        shifts = Shift.query.all()
    # الضابط يمكنه رؤية مناوبات وحدته فقط
    elif current_role == 'officer':
        officer = User.query.get(current_user_id)
        unit_users = User.query.filter_by(unit=officer.unit).all()
        unit_user_ids = [user.id for user in unit_users]
        shifts = Shift.query.filter(Shift.user_id.in_(unit_user_ids)).all()
    # الجندي يمكنه رؤية مناوباته فقط
    else:
        shifts = Shift.query.filter_by(user_id=current_user_id).all()
    
    return jsonify({'shifts': [shift.to_dict() for shift in shifts]}), 200

@shift_bp.route('/shifts', methods=['POST'])
def create_shift():
    # التحقق من الصلاحيات (فقط المدير والقائد والضابط يمكنهم إنشاء مناوبات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander', 'officer']:
        return jsonify({'message': 'غير مصرح لك بإنشاء مناوبات'}), 403
    
    data = request.get_json()
    
    # التحقق من وجود البيانات المطلوبة
    required_fields = ['user_id', 'start_date', 'end_date', 'location', 'type']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'حقل {field} مطلوب'}), 400
    
    # التحقق من وجود المستخدم
    user = User.query.get(data.get('user_id'))
    if not user:
        return jsonify({'message': 'المستخدم غير موجود'}), 404
    
    # إذا كان الضابط، يجب أن يكون المستخدم من نفس الوحدة
    if current_role == 'officer':
        officer = User.query.get(current_user_id)
        if user.unit != officer.unit:
            return jsonify({'message': 'غير مصرح لك بإنشاء مناوبات لعساكر من وحدات أخرى'}), 403
    
    # إنشاء مناوبة جديدة
    new_shift = Shift(
        user_id=data.get('user_id'),
        start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d %H:%M'),
        end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d %H:%M'),
        location=data.get('location'),
        type=data.get('type'),
        status=data.get('status', 'scheduled')
    )
    
    db.session.add(new_shift)
    db.session.commit()
    
    return jsonify({
        'message': 'تم إنشاء المناوبة بنجاح',
        'shift': new_shift.to_dict()
    }), 201

@shift_bp.route('/shifts/<int:shift_id>', methods=['GET'])
def get_shift(shift_id):
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    shift = Shift.query.get(shift_id)
    
    if not shift:
        return jsonify({'message': 'المناوبة غير موجودة'}), 404
    
    # التحقق من صلاحية الوصول للمناوبة
    if current_role in ['admin', 'commander']:
        # المدير والقائد يمكنهم الوصول لجميع المناوبات
        pass
    elif current_role == 'officer':
        # الضابط يمكنه الوصول لمناوبات وحدته فقط
        officer = User.query.get(current_user_id)
        shift_user = User.query.get(shift.user_id)
        if shift_user.unit != officer.unit:
            return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه المناوبة'}), 403
    else:
        # الجندي يمكنه الوصول لمناوباته فقط
        if shift.user_id != current_user_id:
            return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه المناوبة'}), 403
    
    return jsonify({'shift': shift.to_dict()}), 200

@shift_bp.route('/shifts/<int:shift_id>', methods=['PUT'])
def update_shift(shift_id):
    # التحقق من الصلاحيات (فقط المدير والقائد والضابط يمكنهم تعديل المناوبات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander', 'officer']:
        return jsonify({'message': 'غير مصرح لك بتعديل المناوبات'}), 403
    
    shift = Shift.query.get(shift_id)
    
    if not shift:
        return jsonify({'message': 'المناوبة غير موجودة'}), 404
    
    # التحقق من صلاحية تعديل المناوبة
    if current_role == 'officer':
        # الضابط يمكنه تعديل مناوبات وحدته فقط
        officer = User.query.get(current_user_id)
        shift_user = User.query.get(shift.user_id)
        if shift_user.unit != officer.unit:
            return jsonify({'message': 'غير مصرح لك بتعديل هذه المناوبة'}), 403
    
    data = request.get_json()
    
    # تحديث البيانات المسموح بتعديلها
    if 'start_date' in data:
        shift.start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d %H:%M')
    
    if 'end_date' in data:
        shift.end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d %H:%M')
    
    allowed_fields = ['location', 'type', 'status']
    for field in allowed_fields:
        if field in data:
            setattr(shift, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث المناوبة بنجاح',
        'shift': shift.to_dict()
    }), 200

@shift_bp.route('/shifts/<int:shift_id>', methods=['DELETE'])
def delete_shift(shift_id):
    # التحقق من الصلاحيات (فقط المدير والقائد يمكنهم حذف المناوبات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander']:
        return jsonify({'message': 'غير مصرح لك بحذف المناوبات'}), 403
    
    shift = Shift.query.get(shift_id)
    
    if not shift:
        return jsonify({'message': 'المناوبة غير موجودة'}), 404
    
    db.session.delete(shift)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف المناوبة بنجاح'}), 200
