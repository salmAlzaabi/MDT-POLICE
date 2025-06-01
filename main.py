import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session
from src.models.user import db, User
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.violation import violation_bp, Violation
from src.routes.search import search_bp
from src.routes.equipment import equipment_bp, Equipment
from src.routes.shift import shift_bp, Shift
from src.routes.message import message_bp, Message
from datetime import timedelta

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'),
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)

# تسجيل جميع البلوبرنتس
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(violation_bp, url_prefix='/api/violations')
app.register_blueprint(search_bp, url_prefix='/api/search')
app.register_blueprint(equipment_bp, url_prefix='/api/equipment')
app.register_blueprint(shift_bp, url_prefix='/api/shifts')
app.register_blueprint(message_bp, url_prefix='/api/messages')

# تفعيل قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# إنشاء جميع الجداول في قاعدة البيانات
with app.app_context():
    db.create_all()
    
    # إنشاء مستخدم مدير افتراضي إذا لم يكن موجودًا
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            full_name='مدير النظام',
            username='admin',
            email='admin@military.gov',
            rank='عقيد',
            unit='القيادة العامة',
            military_id='ADMIN001',
            role='admin',
            status='active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
