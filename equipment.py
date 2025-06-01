from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from datetime import datetime

equipment_bp = Blueprint('equipment', __name__)

class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='available')  # available, in-use, maintenance, lost
    receive_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_maintenance = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'serial_number': self.serial_number,
            'type': self.type,
            'status': self.status,
            'receive_date': self.receive_date.strftime('%Y-%m-%d'),
            'last_maintenance': self.last_maintenance.strftime('%Y-%m-%d') if self.last_maintenance else None,
            'location': self.location,
            'notes': self.notes
        }

@equipment_bp.route('/equipment', methods=['GET'])
def get_equipment():
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    # المدير والقائد يمكنهم رؤية جميع المعدات
    if current_role in ['admin', 'commander']:
        equipment_list = Equipment.query.all()
    # الضابط يمكنه رؤية معدات وحدته فقط
    elif current_role == 'officer':
        officer = User.query.get(current_user_id)
        equipment_list = Equipment.query.filter_by(location=officer.unit).all()
    # الجندي يمكنه رؤية المعدات المتاحة فقط
    else:
        soldier = User.query.get(current_user_id)
        equipment_list = Equipment.query.filter_by(location=soldier.unit).all()
    
    return jsonify({'equipment': [item.to_dict() for item in equipment_list]}), 200

@equipment_bp.route('/equipment', methods=['POST'])
def create_equipment():
    # التحقق من الصلاحيات (فقط المدير والقائد والضابط يمكنهم إضافة معدات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander', 'officer']:
        return jsonify({'message': 'غير مصرح لك بإضافة معدات'}), 403
    
    data = request.get_json()
    
    # التحقق من وجود البيانات المطلوبة
    required_fields = ['name', 'serial_number', 'type', 'location']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'حقل {field} مطلوب'}), 400
    
    # التحقق من عدم وجود معدة بنفس الرقم التسلسلي
    if Equipment.query.filter_by(serial_number=data.get('serial_number')).first():
        return jsonify({'message': 'الرقم التسلسلي موجود بالفعل'}), 400
    
    # إذا كان الضابط، يجب أن يكون موقع المعدة هو وحدته
    if current_role == 'officer':
        officer = User.query.get(current_user_id)
        if data.get('location') != officer.unit:
            return jsonify({'message': 'غير مصرح لك بإضافة معدات لوحدات أخرى'}), 403
    
    # إنشاء معدة جديدة
    new_equipment = Equipment(
        name=data.get('name'),
        serial_number=data.get('serial_number'),
        type=data.get('type'),
        status=data.get('status', 'available'),
        location=data.get('location'),
        notes=data.get('notes', '')
    )
    
    db.session.add(new_equipment)
    db.session.commit()
    
    return jsonify({
        'message': 'تمت إضافة المعدة بنجاح',
        'equipment': new_equipment.to_dict()
    }), 201

@equipment_bp.route('/equipment/<int:equipment_id>', methods=['GET'])
def get_equipment_item(equipment_id):
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    equipment_item = Equipment.query.get(equipment_id)
    
    if not equipment_item:
        return jsonify({'message': 'المعدة غير موجودة'}), 404
    
    # التحقق من صلاحية الوصول للمعدة
    if current_role in ['admin', 'commander']:
        # المدير والقائد يمكنهم الوصول لجميع المعدات
        pass
    else:
        # الضابط والجندي يمكنهم الوصول لمعدات وحدتهم فقط
        user = User.query.get(current_user_id)
        if equipment_item.location != user.unit:
            return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه المعدة'}), 403
    
    return jsonify({'equipment': equipment_item.to_dict()}), 200

@equipment_bp.route('/equipment/<int:equipment_id>', methods=['PUT'])
def update_equipment(equipment_id):
    # التحقق من الصلاحيات (فقط المدير والقائد والضابط يمكنهم تعديل المعدات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander', 'officer']:
        return jsonify({'message': 'غير مصرح لك بتعديل المعدات'}), 403
    
    equipment_item = Equipment.query.get(equipment_id)
    
    if not equipment_item:
        return jsonify({'message': 'المعدة غير موجودة'}), 404
    
    # التحقق من صلاحية تعديل المعدة
    if current_role == 'officer':
        # الضابط يمكنه تعديل معدات وحدته فقط
        officer = User.query.get(current_user_id)
        if equipment_item.location != officer.unit:
            return jsonify({'message': 'غير مصرح لك بتعديل هذه المعدة'}), 403
    
    data = request.get_json()
    
    # تحديث البيانات المسموح بتعديلها
    allowed_fields = ['name', 'type', 'status', 'location', 'notes', 'last_maintenance']
    
    for field in allowed_fields:
        if field in data:
            setattr(equipment_item, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث المعدة بنجاح',
        'equipment': equipment_item.to_dict()
    }), 200

@equipment_bp.route('/equipment/<int:equipment_id>', methods=['DELETE'])
def delete_equipment(equipment_id):
    # التحقق من الصلاحيات (فقط المدير والقائد يمكنهم حذف المعدات)
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    if current_role not in ['admin', 'commander']:
        return jsonify({'message': 'غير مصرح لك بحذف المعدات'}), 403
    
    equipment_item = Equipment.query.get(equipment_id)
    
    if not equipment_item:
        return jsonify({'message': 'المعدة غير موجودة'}), 404
    
    db.session.delete(equipment_item)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف المعدة بنجاح'}), 200
