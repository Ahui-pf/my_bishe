from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

# 初始化扩展
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    CORS(app, resources={
        r"/*": {
            "origins": ["*"],  # 允许所有来源
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "expose_headers": ["Content-Type", "Authorization"],
            "send_wildcard": True
        }
    })
    db.init_app(app)
    jwt.init_app(app)
    
    # 注册蓝图
    from .routes import auth_bp
    app.register_blueprint(auth_bp)
    
    return app