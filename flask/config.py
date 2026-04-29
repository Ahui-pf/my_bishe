class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/pothole_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = '4qYkj8sLpM3nXv2rTwUz7CbF9GhE5AeD'  # 实际使用时应该使用更安全的密钥生成方式
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # token有效期24小时
    
    # 跨域配置
    CORS_HEADERS = 'Content-Type'