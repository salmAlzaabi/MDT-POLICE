from flask import Blueprint, request, jsonify, session
from src.models.user import User, db

search_bp = Blueprint('search', __name__)

@search_bp.route('/search/users', methods=['GET'])
def search_users():
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    # الحصول على معايير البحث
    query = request.args.get('query', '')
    rank = request.args.get('rank', '')
    unit = request.args.get('unit', '')
    
    # بناء استعلام البحث
    search_query = User.query
    
    if query:
        search_query = search_query.filter(
            (User.full_name.like(f'%{query}%')) |
            (User.username.like(f'%{query}%')) |
            (User.military_id.like(f'%{query}%')) |
            (User.email.like(f'%{query}%'))
        )
    
    if rank:
        search_query = search_query.filter(User.rank == rank)
    
    if unit:
        search_query = search_query.filter(User.unit == unit)
    
    # تطبيق قيود الصلاحيات
    if current_role == 'officer':
        # الضابط يمكنه البحث عن العساكر في وحدته فقط
        officer = User.query.get(current_user_id)
        search_query = search_query.filter(User.unit == officer.unit)
    elif current_role == 'soldier':
        # الجندي يمكنه البحث عن نفسه فقط
        search_query = search_query.filter(User.id == current_user_id)
    
    # تنفيذ البحث
    results = search_query.all()
    
    return jsonify({
        'count': len(results),
        'results': [user.to_dict() for user in results]
    }), 200

@search_bp.route('/search/violations', methods=['GET'])
def search_violations():
    # التحقق من الصلاحيات
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    if not current_user_id:
        return jsonify({'message': 'غير مصرح به'}), 401
    
    # الحصول على معايير البحث
    user_id = request.args.get('user_id', '')
    type = request.args.get('type', '')
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # استيراد نموذج المخالفات
    from src.routes.violation import Violation
    
    # بناء استعلام البحث
    search_query = Violation.query
    
    if user_id:
        search_query = search_query.filter(Violation.user_id == user_id)
    
    if type:
        search_query = search_query.filter(Violation.type == type)
    
    if status:
        search_query = search_query.filter(Violation.status == status)
    
    if date_from:
        search_query = search_query.filter(Violation.date >= date_from)
    
    if date_to:
        search_query = search_query.filter(Violation.date <= date_to)
    
    # تطبيق قيود الصلاحيات
    if current_role == 'officer':
        # الضابط يمكنه البحث عن مخالفات وحدته فقط
        officer = User.query.get(current_user_id)
        unit_users = User.query.filter_by(unit=officer.unit).all()
        unit_user_ids = [user.id for user in unit_users]
        search_query = search_query.filter(Violation.user_id.in_(unit_user_ids))
    elif current_role == 'soldier':
        # الجندي يمكنه البحث عن مخالفاته فقط
        search_query = search_query.filter(Violation.user_id == current_user_id)
    
    # تنفيذ البحث
    results = search_query.all()
    
    return jsonify({
        'count': len(results),
        'results': [violation.to_dict() for violation in results]
    }), 200
