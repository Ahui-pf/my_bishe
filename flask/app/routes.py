from flask import Blueprint, request, jsonify
from app.models import User
from app import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    
    检查Flask服务和数据库连接状态
    
    Returns:
        JSON: 系统健康状态信息
    """
    try:
        # 测试数据库连接
        db.session.execute('SELECT 1')
        db_status = "connected"
    except Exception as e:
        db_status = f"failed: {str(e)}"
    
    return jsonify({
        "status": "healthy",
        "service": "Flask Auth API",
        "database": {
            "status": db_status,
            "type": "MySQL"
        },
        "endpoints": {
            "auth": True,
            "user_management": True,
            "detection_records": True,
            "statistics": True
        }
    })

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 验证必填字段
    if not all(k in data for k in ('username', 'password', 'email')):
        return jsonify({'error': '缺少必要的字段'}), 400
    
    # 验证用户名和邮箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '邮箱已注册'}), 400
    
    # 创建新用户
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': '注册成功'}), 201

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 验证必填字段
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'error': '缺少必要的字段'}), 400
    
    # 验证用户
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'token': access_token,
            'username': user.username,
            'email': user.email
        })
    
    return jsonify({'error': '用户名或密码错误'}), 401

@auth_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
        
    return jsonify({
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat()
    })

@auth_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """获取用户详细信息"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
        
    return jsonify({
        'data': {
            'username': user.username,
            'email': user.email,
            'phone': getattr(user, 'phone', ''),
            'nickname': getattr(user, 'nickname', ''),
            'avatar': getattr(user, 'avatar', ''),
            'created_at': user.created_at.isoformat()
        }
    })

@auth_bp.route('/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """更新用户信息"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 验证必填字段
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    try:
        # 更新用户信息
        if 'username' in data:
            # 检查用户名是否已被其他用户使用
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': '用户名已被使用'}), 400
            user.username = data['username']
        
        if 'email' in data:
            # 检查邮箱是否已被其他用户使用
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': '邮箱已被使用'}), 400
            user.email = data['email']
        
        if 'phone' in data:
            user.phone = data['phone']
        
        if 'nickname' in data:
            user.nickname = data['nickname']
        
        if 'avatar' in data:
            user.avatar = data['avatar']
        
        db.session.commit()
        
        return jsonify({'message': '用户信息更新成功'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

@auth_bp.route('/user/password', methods=['PUT'])
@jwt_required()
def change_password():
    """修改用户密码"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 验证必填字段
    if not all(k in data for k in ('oldPassword', 'newPassword')):
        return jsonify({'error': '缺少必要的字段'}), 400
    
    old_password = data['oldPassword']
    new_password = data['newPassword']
    
    # 验证当前密码
    if not user.check_password(old_password):
        return jsonify({'error': '当前密码错误'}), 400
    
    # 验证新密码强度
    if len(new_password) < 6:
        return jsonify({'error': '新密码长度不能少于6位'}), 400
    
    if len(new_password) > 20:
        return jsonify({'error': '新密码长度不能超过20位'}), 400
    
    # 检查新密码是否包含字母和数字
    if not (any(c.isalpha() for c in new_password) and any(c.isdigit() for c in new_password)):
        return jsonify({'error': '新密码必须包含字母和数字'}), 400
    
    try:
        # 更新密码
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': '密码修改成功'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'密码修改失败: {str(e)}'}), 500

@auth_bp.route('/user/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """获取用户统计信息"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        from app.models import DetectionRecord
        from datetime import datetime, timedelta
        
        # 计算注册天数
        join_days = (datetime.utcnow() - user.created_at).days
        
        # 统计检测记录
        total_detections = DetectionRecord.query.filter_by(user_id=user.id).count()
        image_detections = DetectionRecord.query.filter_by(user_id=user.id, detection_type='image').count()
        video_detections = DetectionRecord.query.filter_by(user_id=user.id, detection_type='video').count()
        
        # 计算最后登录时间（这里简化处理，实际应该记录登录时间）
        last_login = "今天"  # 可以后续扩展记录实际登录时间
        
        return jsonify({
            'totalDetections': total_detections,
            'totalImages': image_detections,
            'totalVideos': video_detections,
            'joinDays': join_days,
            'lastLogin': last_login
        })
        
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

@auth_bp.route('/user/settings', methods=['GET'])
@jwt_required()
def get_user_settings():
    """获取用户设置"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        # 返回默认设置，后续可以扩展为从数据库获取
        return jsonify({
            'data': {
                'defaultConf': 0.25,
                'defaultIou': 0.45,
                'defaultReturnImage': True,
                'defaultFrameStride': 1,
                'defaultMaxFrames': 0
            }
        })
    except Exception as e:
        return jsonify({'error': f'获取用户设置失败: {str(e)}'}), 500

@auth_bp.route('/user/settings', methods=['PUT'])
@jwt_required()
def update_user_settings():
    """更新用户设置"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    try:
        # 这里可以扩展为保存到数据库
        # 目前只是返回成功消息
        return jsonify({'message': '用户设置更新成功'})
    except Exception as e:
        return jsonify({'error': f'更新用户设置失败: {str(e)}'}), 500

@auth_bp.route('/user/detection-record', methods=['POST'])
@jwt_required()
def create_detection_record():
    """创建检测记录"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['file_name', 'detection_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必要的字段'}), 400
    
    try:
        from app.models import DetectionRecord
        
        # 创建检测记录
        record = DetectionRecord(
            user_id=user_id,
            file_name=data['file_name'],
            detection_type=data['detection_type'],
            result_path=data.get('result_path', ''),
            target_count=data.get('target_count', 0),
            conf_threshold=data.get('conf_threshold', 0.25),
            iou_threshold=data.get('iou_threshold', 0.45)
        )
        
        db.session.add(record)
        db.session.commit()
        return jsonify({'message': '检测记录保存成功', 'record_id': record.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'保存检测记录失败: {str(e)}'}), 500

@auth_bp.route('/user/detection-history', methods=['GET'])
@jwt_required()
def get_detection_history():
    """获取检测历史"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        from app.models import DetectionRecord
        
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 查询检测记录
        records = DetectionRecord.query.filter_by(user_id=user_id)\
            .order_by(DetectionRecord.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        # 转换为字典格式
        history = []
        for record in records:
            history.append({
                'id': record.id,
                'file_name': record.file_name,
                'detection_type': record.detection_type,
                'result_path': record.result_path,
                'target_count': record.target_count,
                'conf_threshold': record.conf_threshold,
                'iou_threshold': record.iou_threshold,
                'created_at': record.created_at.isoformat() + 'Z'  # 添加UTC标识
            })
        
        return jsonify(history)
        
    except Exception as e:
        return jsonify({'error': f'获取检测历史失败: {str(e)}'}), 500

@auth_bp.route('/user/detection-records', methods=['GET'])
@jwt_required()
def get_detection_records():
    """获取检测记录（用于报告生成）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        from app.models import DetectionRecord
        from datetime import datetime
        
        # 获取查询参数
        limit = request.args.get('limit', 100, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = DetectionRecord.query.filter_by(user_id=user_id)
        
        # 添加日期过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(DetectionRecord.created_at >= start_dt)
            except ValueError:
                return jsonify({'error': '开始日期格式错误，请使用YYYY-MM-DD'}), 400
                
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # 包含整个结束日期
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(DetectionRecord.created_at <= end_dt)
            except ValueError:
                return jsonify({'error': '结束日期格式错误，请使用YYYY-MM-DD'}), 400
        
        # 执行查询
        records = query.order_by(DetectionRecord.created_at.desc()).limit(limit).all()
        
        # 转换为字典格式
        records_data = []
        for record in records:
            records_data.append({
                'id': record.id,
                'file_name': record.file_name,
                'detection_type': record.detection_type,
                'result_path': record.result_path,
                'target_count': record.target_count,
                'conf_threshold': record.conf_threshold,
                'iou_threshold': record.iou_threshold,
                'created_at': record.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'records': records_data,
            'count': len(records_data)
        })
        
    except Exception as e:
        print(f"获取检测记录时出错: {str(e)}")
        return jsonify({'error': f'获取检测记录失败: {str(e)}'}), 500