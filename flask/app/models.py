from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    nickname = db.Column(db.String(80), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    detection_records = db.relationship('DetectionRecord', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class DetectionRecord(db.Model):
    __tablename__ = 'detection_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    detection_type = db.Column(db.Enum('image', 'video'), nullable=False)
    result_path = db.Column(db.String(255))
    target_count = db.Column(db.Integer, default=0)
    conf_threshold = db.Column(db.Float, default=0.25)
    iou_threshold = db.Column(db.Float, default=0.45)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)