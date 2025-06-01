from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from datetime import datetime

message_bp = Blueprint('message', __name__)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    send_date = db.Column(db.DateTime, default=datetime.utcnow)
    read_status = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='normal')  # normal, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'subject': self.subject,
            'content': self.content,
            'send_date': self.send_date.strftime('%Y-%m-%d %H:%M'),
            'read_status': self.read_status,
            'priority': self.priority
        }

@message_bp.route('/messages', methods=['GET'])
def get_messages():
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    # الحصول على معايير التصفية
    message_type = request.args.get('type', 'inbox')  # inbox, sent, all
    
    # بناء استعلام البحث
    if message_type == 'inbox':
        messages = Message.query.filter_by(receiver_id=current_user_id).order_by(Message.send_date.desc()).all()
    elif message_type == 'sent':
        messages = Message.query.filter_by(sender_id=current_user_id).order_by(Message.send_date.desc()).all()
    else:  # all
        messages = Message.query.filter(
            (Message.receiver_id == current_user_id) | (Message.sender_id == current_user_id)
        ).order_by(Message.send_date.desc()).all()
    
    return jsonify({'messages': [message.to_dict() for message in messages]}), 200

@message_bp.route('/messages', methods=['POST'])
def send_message():
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    data = request.get_json()
    
    # التحقق من وجود البيانات المطلوبة
    required_fields = ['receiver_id', 'subject', 'content']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'حقل {field} مطلوب'}), 400
    
    # التحقق من وجود المستلم
    receiver = User.query.get(data.get('receiver_id'))
    if not receiver:
        return jsonify({'message': 'المستلم غير موجود'}), 404
    
    # إنشاء رسالة جديدة
    new_message = Message(
        sender_id=current_user_id,
        receiver_id=data.get('receiver_id'),
        subject=data.get('subject'),
        content=data.get('content'),
        priority=data.get('priority', 'normal')
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({
        'message': 'تم إرسال الرسالة بنجاح',
        'message_data': new_message.to_dict()
    }), 201

@message_bp.route('/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    message = Message.query.get(message_id)
    
    if not message:
        return jsonify({'message': 'الرسالة غير موجودة'}), 404
    
    # التحقق من صلاحية الوصول للرسالة
    if message.sender_id != current_user_id and message.receiver_id != current_user_id:
        return jsonify({'message': 'غير مصرح لك بالوصول إلى هذه الرسالة'}), 403
    
    # تحديث حالة القراءة إذا كان المستخدم هو المستلم
    if message.receiver_id == current_user_id and not message.read_status:
        message.read_status = True
        db.session.commit()
    
    return jsonify({'message': message.to_dict()}), 200

@message_bp.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    message = Message.query.get(message_id)
    
    if not message:
        return jsonify({'message': 'الرسالة غير موجودة'}), 404
    
    # التحقق من صلاحية حذف الرسالة
    if message.sender_id != current_user_id and message.receiver_id != current_user_id:
        return jsonify({'message': 'غير مصرح لك بحذف هذه الرسالة'}), 403
    
    db.session.delete(message)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف الرسالة بنجاح'}), 200
