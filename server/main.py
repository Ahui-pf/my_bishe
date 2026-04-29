from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.websockets import WebSocketState
from typing import Optional, List, Dict, Any, Union
import uvicorn
from jose import jwt, JWTError
import io
import json
import base64
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
import cv2
from datetime import datetime, timedelta, timezone
from enum import Enum
import requests
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
from collections import Counter
import statistics

# 将 yolov9 源码路径加入 sys.path
ROOT = Path(__file__).resolve().parents[1] / 'Yolov9' / 'yolov9-pothole'
sys.path.append(str(ROOT))

# 数据库配置
FLASK_API_BASE_URL = "http://localhost:5000"  # Flask服务的地址

import torch  # noqa: E402
from models.common import DetectMultiBackend, AutoShape  # noqa: E402
from utils.general import non_max_suppression, scale_boxes  # noqa: E402

# JWT 配置
SECRET_KEY = "4qYkj8sLpM3nXv2rTwUz7CbF9GhE5AeD"  # 与 Flask 服务使用相同的密钥
ALGORITHM = "HS256"

app = FastAPI()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # 添加其他可能的前端端口
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,  # 允许跨域请求携带凭证
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明确指定允许的方法
    allow_headers=[
        "Authorization", 
        "Content-Type", 
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
        "If-Modified-Since"
    ],
    expose_headers=["*"]  # 允许前端访问响应头
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求的中间件"""
    try:
        response = await call_next(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"处理请求时出错: {str(e)}")
        raise

# 全局模型
model_autoshape = None
model_names: List[str] = []
imgsz_default = (640, 640)

# 检测类型枚举
class DetectionType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    REALTIME = "realtime"

# 认证中间件
security = HTTPBearer()


def parse_record_created_at(value: Any) -> Optional[datetime]:
    """Parse record timestamps returned by Flask."""
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    return None


def record_sort_timestamp(record: Dict[str, Any]) -> float:
    created_at = parse_record_created_at(record.get("created_at"))
    if created_at is None:
        return 0.0

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return created_at.timestamp()


def sort_detection_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(records, key=record_sort_timestamp, reverse=True)


def build_flask_access_token(user_id: int) -> str:
    current_timestamp = int(datetime.now(timezone.utc).timestamp())
    token_payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": current_timestamp,
        "exp": current_timestamp + 3600
    }
    return jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_user_detection_records(
    user_id: int,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auth_token: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    获取用户的检测记录（通过Flask API）
    
    Args:
        user_id: 用户ID
        limit: 返回记录数限制
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        List[Dict[str, Any]] | None: 检测记录列表或None
    """
    try:
        flask_token = None
        if auth_token:
            normalized = auth_token.strip()
            if normalized.lower().startswith("bearer "):
                normalized = normalized.split(" ", 1)[1].strip()
            flask_token = normalized
        else:
            flask_token = build_flask_access_token(user_id)
        
        # 构造请求参数
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        # 调用Flask API获取记录
        headers = {
            "Authorization": f"Bearer {flask_token}",
            "Content-Type": "application/json"
        }
        
        print(f"🔄 获取用户{user_id}的检测记录")
        print(f"📡 调用Flask API: {FLASK_API_BASE_URL}/user/detection-records")
        print(f"📦 请求参数: {params}")
        
        response = requests.get(
            f"{FLASK_API_BASE_URL}/user/detection-records",
            params=params,
            headers=headers,
            timeout=10
        )
        
        print(f"📥 Flask API响应: 状态码={response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"📄 响应数据结构: {list(response_data.keys()) if isinstance(response_data, dict) else type(response_data)}")
            
            if response_data.get('success'):
                records = sort_detection_records(response_data.get('records', []))
                print(f"✅ 成功获取{len(records)}条检测记录")
                if len(records) > 0:
                    print(f"🔍 最新记录示例: {records[0]}")
                return records
            else:
                print(f"❌ Flask API返回业务错误: {response_data}")
                return None
        elif response.status_code == 401:
            print(f"❌ 获取检测记录失败: 认证错误")
            print(f"🔍 响应内容: {response.text}")
            return None
        else:
            print(f"❌ 获取检测记录失败: HTTP {response.status_code}")
            print(f"🔍 响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"获取检测记录时出错: {str(e)}")
        return None

async def save_detection_record(
    user_id: int,
    file_name: str,
    detection_type: str,
    target_count: int,
    conf_threshold: float,
    iou_threshold: float,
    auth_token: Optional[str] = None
) -> bool:
    """
    保存检测记录到数据库（通过Flask API）
    
    Args:
        user_id: 用户ID
        file_name: 文件名
        detection_type: 检测类型（image/video）
        target_count: 检测到的目标数量
        conf_threshold: 置信度阈值
        iou_threshold: IoU阈值
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 准备数据
        record_data = {
            "file_name": file_name,
            "detection_type": detection_type.value if isinstance(detection_type, Enum) else str(detection_type),
            "target_count": target_count,
            "conf_threshold": conf_threshold,
            "iou_threshold": iou_threshold,
            "result_path": ""  # 可以根据需要设置结果路径
        }
        
        if auth_token:
            normalized = auth_token.strip()
            if normalized.lower().startswith("bearer "):
                normalized = normalized.split(" ", 1)[1].strip()
            flask_token = normalized
        else:
            flask_token = build_flask_access_token(user_id)
        
        # 调用Flask API保存记录
        headers = {
            "Authorization": f"Bearer {flask_token}",
            "Content-Type": "application/json"
        }
        
        print(f"🔄 保存检测记录: 用户{user_id}, 文件{file_name}, 类型{detection_type}, 目标数{target_count}")
        print(f"📡 调用Flask API: {FLASK_API_BASE_URL}/user/detection-record")
        print(f"📦 发送数据: {record_data}")
        
        response = requests.post(
            f"{FLASK_API_BASE_URL}/user/detection-record",
            json=record_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📥 Flask API响应: 状态码={response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 检测记录保存成功: {response.json()}")
            return True
        elif response.status_code == 401:
            print(f"❌ 检测记录保存失败: Token认证失败")
            print(f"🔍 响应内容: {response.text}")
            return False
        else:
            print(f"❌ 检测记录保存失败: HTTP {response.status_code}")
            print(f"🔍 响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"保存检测记录时出错: {str(e)}")
        return False


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """验证 JWT 令牌并返回用户 ID
    
    Args:
        credentials: Bearer token 凭证
        
    Returns:
        int: 用户 ID
        
    Raises:
        HTTPException: 认证失败时抛出 401/403 错误
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="未提供认证凭证"
        )

    try:
        token = credentials.credentials
        
        # 尝试直接解析令牌
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get('sub')
            if user_id:
                # 确保用户ID是整数
                user_id_int = int(user_id) if isinstance(user_id, (str, int)) else None
                if user_id_int:
                    return user_id_int
        except Exception as e:
            pass
            
        # 尝试手动解码令牌负载
        try:
            parts = token.split('.')
            if len(parts) != 3:
                raise ValueError(f"无效的JWT格式，应该有3部分，实际有{len(parts)}部分")
            
            header, payload_b64, signature = parts
            # 添加 padding
            payload_b64 += '=' * (-len(payload_b64) % 4)
            # 解码并解析 JSON
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes)
            
            # 检查已知的用户ID字段
            user_id = None
            for field in ['sub', 'identity', 'user_id', 'id']:
                if field in payload:
                    user_id = payload[field]
                    break
                    
            if not user_id:
                raise ValueError("未在令牌中找到用户ID (检查了 sub, identity, user_id, id)")
            
            # 检查令牌类型（可选）
            token_type = payload.get('type', 'access')
            
            if token_type not in ('access', 'bearer', None):
                pass
            
            return int(user_id)
            
        except Exception as e:
            raise ValueError(f"令牌解析失败: {str(e)}")
            
    except ValueError as e:
        print(f"验证失败: {str(e)}")
        raise HTTPException(
            status_code=403, 
            detail=str(e)
        )
    except Exception as e:
        print(f"未预期的错误: {str(e)}")
        raise HTTPException(
            status_code=403,
            detail=f"认证失败: {str(e)}"
        )



def load_model(weights_path: Optional[str] = None, device: str = "") -> None:
    global model_autoshape, model_names
    weights = Path(weights_path) if weights_path else ROOT / 'yolo.pt'
    # 自动选择设备：优先 GPU(0)，否则 CPU
    device_str = device.strip() if isinstance(device, str) else ""
    if not device_str:
        device_str = "0" if torch.cuda.is_available() else "cpu"
    model = DetectMultiBackend(weights=str(weights), device=device_str, dnn=False, data=ROOT / 'data/coco.yaml', fp16=False)
    model_autoshape = AutoShape(model)  # 处理多种输入并内置预处理
    model_names = model.names if hasattr(model, 'names') else getattr(model, 'module', {}).names
    try:
        print(f"[startup] model loaded on device={device_str}, classes={len(model_names)}")
    except Exception:
        print(f"[startup] model loaded on device={device_str}")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点
    
    检查系统各项组件的运行状态：
    - AI模型加载状态
    - 数据库连接状态
    - Flask API连接状态
    
    Returns:
        Dict[str, Any]: 系统健康状态信息
    """
    # 检查Flask API连接状态
    flask_status = "unknown"
    flask_details = {}
    try:
        print(f"检查Flask API健康状态: {FLASK_API_BASE_URL}/health")
        response = requests.get(f"{FLASK_API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            flask_status = "connected"
            flask_details = {"message": "Flask API连接正常"}
        else:
            flask_status = f"error_{response.status_code}"
            flask_details = {"message": f"Flask API返回错误状态: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        flask_status = "disconnected"
        flask_details = {"message": "Flask API服务未启动或无法连接", "suggestion": "请确保Flask服务在端口5000运行"}
    except requests.exceptions.Timeout:
        flask_status = "timeout"
        flask_details = {"message": "连接Flask API超时"}
    except Exception as e:
        flask_status = "failed"
        flask_details = {"message": f"连接错误: {str(e)}"}
    
    return {
        "status": "healthy",
        "ai_model": {
            "loaded": model_autoshape is not None,
            "classes": len(model_names) if model_names else 0,
            "image_size": imgsz_default
        },
        "flask_api": {
            "status": flask_status,
            "url": FLASK_API_BASE_URL,
            "details": flask_details
        },
        "features": {
            "image_detection": True,
            "video_detection": True,
            "database_logging": flask_status == "connected"  # 只有在Flask API连接正常时才启用数据库记录
        }
    }

@app.get("/auth/verify")
async def verify_auth_status(current_user_id: int = Depends(verify_token)) -> Dict[str, Any]:
    """
    验证当前认证状态
    
    Returns:
        Dict[str, Any]: 认证状态信息
    """
    return {
        "authenticated": True,
        "user_id": current_user_id,
        "message": "认证有效"
    }

def generate_detection_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    生成检测统计数据
    
    Args:
        records: 检测记录列表
        
    Returns:
        Dict[str, Any]: 统计数据
    """
    if not records:
        return {
            "total_detections": 0,
            "total_targets": 0,
            "detection_types": {},
            "average_targets_per_detection": 0,
            "confidence_stats": {
                "average": 0.25,
                "min": 0.25,
                "max": 0.25,
                "most_common": 0.25
            },
            "date_range": {},
            "file_types": {},
            "target_stats": {
                "total": 0,
                "average": 0,
                "max_in_single": 0,
                "zero_detections": 0
            },
            "success_rate": 0  # 添加缺失的字段
        }
    
    # 基础统计
    total_detections = len(records)
    total_targets = sum(record.get('target_count', 0) for record in records)
    
    # 按检测类型统计
    detection_types = Counter(record.get('detection_type', 'unknown') for record in records)
    
    # 按文件类型统计
    file_types = Counter()
    for record in records:
        file_name = record.get('file_name', '')
        if '.' in file_name:
            ext = file_name.split('.')[-1].lower()
            file_types[ext] += 1
        else:
            file_types['unknown'] += 1
    
    # 置信度统计
    conf_thresholds = [record.get('conf_threshold', 0.25) for record in records if record.get('conf_threshold')]
    confidence_stats = {
        "average": round(statistics.mean(conf_thresholds), 3) if conf_thresholds else 0.25,
        "min": round(min(conf_thresholds), 3) if conf_thresholds else 0.25,
        "max": round(max(conf_thresholds), 3) if conf_thresholds else 0.25,
        "most_common": round(statistics.mode(conf_thresholds), 3) if conf_thresholds else 0.25
    }
    
    # 日期范围统计
    dates = []
    for record in records:
        date_obj = parse_record_created_at(record.get('created_at'))
        if date_obj:
            # 假设日期格式为ISO 8601
            dates.append(date_obj)
    
    date_range = {}
    if dates:
        date_range = {
            "start_date": min(dates).strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": max(dates).strftime("%Y-%m-%d %H:%M:%S"),
            "span_days": (max(dates) - min(dates)).days + 1
        }
    
    # 目标数量统计
    target_counts = [record.get('target_count', 0) for record in records]
    target_stats = {
        "total": total_targets,
        "average": round(statistics.mean(target_counts), 2) if target_counts else 0,
        "max_in_single": max(target_counts) if target_counts else 0,
        "zero_detections": sum(1 for count in target_counts if count == 0)
    }
    
    return {
        "total_detections": total_detections,
        "total_targets": total_targets,
        "average_targets_per_detection": round(total_targets / max(total_detections, 1), 2),
        "detection_types": dict(detection_types),
        "file_types": dict(file_types),
        "confidence_stats": confidence_stats,
        "date_range": date_range,
        "target_stats": target_stats,
        "success_rate": round((total_detections - target_stats["zero_detections"]) / max(total_detections, 1) * 100, 2)
    }

def create_report_pdf(user_id: int, statistics: Dict[str, Any], records: List[Dict[str, Any]], api_connected: bool = True) -> str:
    """
    创建PDF检测报告
    
    Args:
        user_id: 用户ID
        statistics: 统计数据
        records: 检测记录
        api_connected: API是否连接正常
        
    Returns:
        str: PDF文件的base64编码
    """
    # 创建临时PDF文件 - Windows兼容性改进
    try:
        # 优先使用当前目录的临时文件
        import uuid
        temp_filename = f"temp_report_{uuid.uuid4().hex[:8]}.pdf"
        
        # 尝试在server目录下创建临时文件
        if os.path.exists("server"):
            pdf_path = os.path.join("server", temp_filename)
        else:
            # 如果不在项目根目录，使用当前目录
            pdf_path = temp_filename
            
    except Exception:
        # 回退到系统临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name
    
    try:
        print(f"开始生成PDF报告，统计数据keys: {list(statistics.keys())}")
        print(f"记录数量: {len(records)}")
        
        # 注册中文字体
        chinese_font_registered = False
        try:
            # 1. 优先检查项目fonts目录
            fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
            project_fonts = [
                os.path.join(fonts_dir, "chinese_font.ttf"),
                os.path.join(fonts_dir, "simhei.ttf"),
                os.path.join(fonts_dir, "simsun.ttf"),
            ]
            
            for font_path in project_fonts:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    chinese_font_registered = True
                    print(f"成功注册项目字体: {font_path}")
                    break
            
            # 2. 如果项目目录没有字体，尝试系统字体
            if not chinese_font_registered:
                import platform
                if platform.system() == "Windows":
                    system_fonts = [
                        "C:/Windows/Fonts/simhei.ttf",  # 黑体
                        "C:/Windows/Fonts/simsun.ttc",  # 宋体
                        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
                        "C:/Windows/Fonts/simkai.ttf",  # 楷体
                    ]
                    
                    for font_path in system_fonts:
                        if os.path.exists(font_path):
                            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                            chinese_font_registered = True
                            print(f"成功注册系统字体: {font_path}")
                            break
            
            if not chinese_font_registered:
                print("未找到中文字体，PDF将使用英文显示")
                print("提示：可将中文字体文件放在server/fonts/目录下")
        except Exception as e:
            print(f"中文字体注册失败: {e}")
            
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # 创建中文样式
        if chinese_font_registered:
            # 创建支持中文的样式
            chinese_title_style = ParagraphStyle(
                'ChineseTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,  # 居中
                fontName='ChineseFont'
            )
            
            chinese_heading_style = ParagraphStyle(
                'ChineseHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=12,
                fontName='ChineseFont'
            )
            
            chinese_normal_style = ParagraphStyle(
                'ChineseNormal',
                parent=styles['Normal'],
                fontSize=10,
                fontName='ChineseFont'
            )
        else:
            # 使用默认样式
            chinese_title_style = styles['Heading1']
            chinese_heading_style = styles['Heading2']
            chinese_normal_style = styles['Normal']
        
        story = []
        
        # 标题
        if chinese_font_registered:
            story.append(Paragraph("坑洞检测报告", chinese_title_style))
        else:
            story.append(Paragraph("Pothole Detection Report", styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # 报告基本信息
        if chinese_font_registered:
            info_data = [
                ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["用户ID", str(user_id)],
                ["统计周期", f"{statistics['date_range'].get('start_date', 'N/A')} 至 {statistics['date_range'].get('end_date', 'N/A')}"],
                ["报告版本", "v1.0"]
            ]
        else:
            info_data = [
                ["Generated Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["User ID", str(user_id)],
                ["Period", f"{statistics['date_range'].get('start_date', 'N/A')} to {statistics['date_range'].get('end_date', 'N/A')}"],
                ["Version", "v1.0"]
            ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        # 为表格设置字体
        table_font = 'ChineseFont' if chinese_font_registered else 'Helvetica'
        table_font_bold = 'ChineseFont' if chinese_font_registered else 'Helvetica-Bold'
        
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), table_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), table_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # 统计摘要
        if chinese_font_registered:
            story.append(Paragraph("检测统计摘要", chinese_heading_style))
        else:
            story.append(Paragraph("Detection Statistics Summary", styles['Heading2']))
        
        # 安全获取统计数据，提供默认值
        total_detections = statistics.get('total_detections', 0)
        total_targets = statistics.get('total_targets', 0)
        avg_targets = statistics.get('average_targets_per_detection', 0)
        success_rate = statistics.get('success_rate', 0)
        conf_stats = statistics.get('confidence_stats', {})
        avg_confidence = conf_stats.get('average', 0.25)
        
        if chinese_font_registered:
            summary_data = [
                ["指标", "数值"],
                ["总检测次数", str(total_detections)],
                ["检测到的目标总数", str(total_targets)],
                ["平均每次检测目标数", str(avg_targets)],
                ["检测成功率", f"{success_rate}%"],
                ["平均置信度阈值", str(avg_confidence)]
            ]
        else:
            summary_data = [
                ["Metric", "Value"],
                ["Total Detections", str(total_detections)],
                ["Total Targets Detected", str(total_targets)],
                ["Avg Targets Per Detection", str(avg_targets)],
                ["Success Rate", f"{success_rate}%"],
                ["Avg Confidence Threshold", str(avg_confidence)]
            ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), table_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), table_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # 检测类型分布
        detection_types = statistics.get('detection_types', {})
        if detection_types:
            if chinese_font_registered:
                story.append(Paragraph("检测类型分布", chinese_heading_style))
                type_data = [["类型", "数量", "占比"]]
            else:
                story.append(Paragraph("Detection Type Distribution", styles['Heading2']))
                type_data = [["Type", "Count", "Percentage"]]
                
            total = statistics.get('total_detections', 0)
            for det_type, count in detection_types.items():
                percentage = round(count / total * 100, 1) if total > 0 else 0
                # 翻译检测类型
                if chinese_font_registered:
                    det_type_display = det_type
                else:
                    type_translation = {
                        'image': 'Image',
                        'video': 'Video', 
                        'realtime': 'Real-time'
                    }
                    det_type_display = type_translation.get(det_type, det_type)
                type_data.append([det_type_display, str(count), f"{percentage}%"])
            
            type_table = Table(type_data, colWidths=[2*inch, 1*inch, 1*inch])
            type_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), table_font_bold),
                ('FONTNAME', (0, 1), (-1, -1), table_font),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(type_table)
            story.append(Spacer(1, 20))
        
        # 最近检测记录部分
        if chinese_font_registered:
            story.append(Paragraph("最近检测记录", chinese_heading_style))
        else:
            story.append(Paragraph("Recent Detection Records", styles['Heading2']))
        
        if records and len(records) > 0:
            # 有真实数据时显示检测记录表格
            if chinese_font_registered:
                record_data = [["文件名", "类型", "目标数", "时间"]]
            else:
                record_data = [["File Name", "Type", "Targets", "Time"]]
            
            # 只显示最近10条记录
            recent_records = records[:10] if len(records) > 10 else records
            for record in recent_records:
                created_at = record.get('created_at', 'N/A')
                parsed_created_at = parse_record_created_at(created_at)
                if parsed_created_at:
                    created_at = parsed_created_at.strftime("%Y-%m-%d %H:%M")
                
                record_data.append([
                    record.get('file_name', 'N/A')[:25],  # 稍微增加文件名长度
                    record.get('detection_type', 'N/A'),
                    str(record.get('target_count', 0)),
                    created_at
                ])
            
            record_table = Table(record_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.5*inch])
            record_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), table_font_bold),
                ('FONTNAME', (0, 1), (-1, -1), table_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(record_table)
            
        else:
            # 没有检测记录时显示提示信息
            if not api_connected:
                # API连接失败
                if chinese_font_registered:
                    no_data_text = "无法获取检测记录数据（数据库连接失败）"
                    suggestion_text = "请确保Flask数据服务正常运行，然后重新生成报告"
                else:
                    no_data_text = "Unable to retrieve detection records (database connection failed)"
                    suggestion_text = "Please ensure Flask data service is running and regenerate the report"
            else:
                # API连接正常但没有数据
                if chinese_font_registered:
                    no_data_text = "暂无检测记录"
                    suggestion_text = "开始使用坑洞检测功能后，您的检测记录将显示在这里"
                else:
                    no_data_text = "No detection records found"
                    suggestion_text = "Your detection records will appear here after using the pothole detection features"
            
            # 创建提示信息的表格
            if chinese_font_registered:
                no_data_table_data = [
                    ["状态", "说明"],
                    [no_data_text, suggestion_text]
                ]
            else:
                no_data_table_data = [
                    ["Status", "Description"],
                    [no_data_text, suggestion_text]
                ]
            
            no_data_table = Table(no_data_table_data, colWidths=[2*inch, 4*inch])
            no_data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), table_font_bold),
                ('FONTNAME', (0, 1), (-1, -1), table_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            story.append(no_data_table)
        
        # 生成PDF
        doc.build(story)
        
        # 读取PDF文件并转换为base64
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        return pdf_base64
        
    except Exception as e:
        print(f"生成PDF报告时出错: {str(e)}")
        raise
    finally:
        # 清理临时文件
        try:
            os.unlink(pdf_path)
        except:
            pass

@app.get("/report/detection-records")
async def get_detection_records(
    request: Request,
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user_id: int = Depends(verify_token)
) -> Dict[str, Any]:
    """
    获取用户检测记录
    
    Args:
        limit: 返回记录数限制
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        current_user_id: 当前用户ID
        
    Returns:
        Dict[str, Any]: 检测记录和统计信息
    """
    try:
        auth_header = request.headers.get("Authorization")
        auth_header = request.headers.get("Authorization")
        records = await get_user_detection_records(
            user_id=current_user_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            auth_token=auth_header
        )

        if records is None:
            raise HTTPException(
                status_code=503,
                detail="Unable to load live detection records from the database service."
            )
        
        statistics = generate_detection_statistics(records)
        
        return {
            "success": True,
            "records": records,
            "statistics": statistics,
            "count": len(records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取检测记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取检测记录失败: {str(e)}")

@app.post("/report/generate")
async def generate_detection_report(
    request: Request,
    format: str = Form("json"),  # json, pdf
    limit: int = Form(100),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    current_user_id: int = Depends(verify_token)
) -> Dict[str, Any]:
    """
    生成检测报告
    
    Args:
        format: 报告格式 (json/pdf)
        limit: 记录数限制
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        current_user_id: 当前用户ID
        
    Returns:
        Dict[str, Any]: 生成的报告数据
    """
    try:
        print(f"用户{current_user_id}请求生成{format}格式的检测报告")
        print(f"请求参数: limit={limit}, start_date={start_date}, end_date={end_date}")
        
        # 首先检查Flask API连接状态
        try:
            flask_health = requests.get(f"{FLASK_API_BASE_URL}/health", timeout=5)
            if flask_health.status_code == 200:
                print(f"Flask API连接正常")
            else:
                print(f"Flask API健康检查失败: {flask_health.status_code}")
        except Exception as e:
            print(f"Flask API连接检查失败: {str(e)}")
        
        # 获取检测记录
        print(f"开始从Flask API获取检测记录...")
        auth_header = request.headers.get("Authorization")
        records = await get_user_detection_records(
            user_id=current_user_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            auth_token=auth_header
        )
        
        api_connected = records is not None
        if not api_connected:
            raise HTTPException(
                status_code=503,
                detail="Unable to load live detection records from the database service."
            )

        has_real_data = len(records) > 0
        print(f"Report source status: api_connected={api_connected}, has_real_data={has_real_data}, record_count={len(records)}")
        statistics = generate_detection_statistics(records)
        
        report_data = {
            "success": True,
            "report_info": {
                "user_id": current_user_id,
                "generated_at": datetime.now().isoformat(),
                "format": format,
                "record_count": len(records),
                "data_source": "live_database",
                "date_range": {
                    "start": start_date,
                    "end": end_date
                }
            },
            "statistics": statistics,
            "records": records[:10] if format == "json" else records  # JSON格式只返回最近10条
        }
        
        if format.lower() == "pdf":
            # 检查PDF生成依赖和兼容性
            try:
                import reportlab
                import matplotlib
                import sys
                print(f"Python版本: {sys.version}")
                print(f"PDF依赖检查: reportlab={getattr(reportlab, '__version__', '未知')}, matplotlib={getattr(matplotlib, '__version__', '未知')}")
                
                # 测试reportlab兼容性
                try:
                    from reportlab.platypus import SimpleDocTemplate
                    from reportlab.lib.pagesizes import A4
                    # 创建一个测试文档来检查兼容性
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=True) as test_file:
                        test_doc = SimpleDocTemplate(test_file.name, pagesize=A4)
                    print("reportlab兼容性测试通过")
                except Exception as compat_e:
                    print(f"reportlab兼容性问题: {str(compat_e)}")
                    if "usedforsecurity" in str(compat_e).lower():
                        raise HTTPException(
                            status_code=500,
                            detail="PDF生成库版本不兼容，请尝试: pip install reportlab==3.6.0"
                        )
                    raise compat_e
                    
            except ImportError as e:
                print(f"PDF依赖缺失: {str(e)}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"PDF报告生成依赖缺失，请安装: pip install reportlab matplotlib"
                )
            
            # 生成PDF报告
            try:
                print(f"开始生成PDF报告...")
                pdf_base64 = create_report_pdf(current_user_id, statistics, records, api_connected=api_connected)
                report_data["pdf_content"] = f"data:application/pdf;base64,{pdf_base64}"
                report_data["download_filename"] = f"detection_report_{current_user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                # PDF格式不返回详细records，减少数据量
                del report_data["records"]
                print(f"PDF报告生成成功，大小: {len(pdf_base64)/1024:.1f}KB")
            except Exception as e:
                print(f"PDF生成失败: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # 如果是兼容性问题，提供JSON备用方案
                if "usedforsecurity" in str(e).lower() or "openssl" in str(e).lower():
                    print("检测到PDF生成兼容性问题，切换到JSON格式...")
                    # 强制切换到JSON格式
                    report_data["format"] = "json"
                    report_data["error"] = "PDF生成失败，已切换到JSON格式"
                    report_data["suggestion"] = "请尝试安装兼容版本: pip install reportlab==3.6.0"
                    print("已生成JSON格式报告作为备用方案")
                else:
                    raise HTTPException(status_code=500, detail=f"PDF报告生成失败: {str(e)}")
        
        print(f"检测报告生成完成: 格式={format}, 记录数={len(records)}, 统计数据完整")
        return report_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"生成检测报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成检测报告失败: {str(e)}")

@app.get("/report/summary")
async def get_detection_summary(
    request: Request,
    days: int = 30,
    current_user_id: int = Depends(verify_token)
) -> Dict[str, Any]:
    """
    获取检测统计摘要
    
    Args:
        days: 统计最近几天的数据
        current_user_id: 当前用户ID
        
    Returns:
        Dict[str, Any]: 统计摘要数据
    """
    try:
        # 计算日期范围
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        print(f"获取用户{current_user_id}最近{days}天的检测摘要")
        
        # 获取检测记录
        auth_header = request.headers.get("Authorization")
        records = await get_user_detection_records(
            user_id=current_user_id,
            limit=1000,  # 获取更多记录用于统计
            start_date=start_date,
            end_date=end_date,
            auth_token=auth_header
        )
        
        if records is None:
            raise HTTPException(
                status_code=503,
                detail="Unable to load live detection summary from the database service."
            )
        statistics = generate_detection_statistics(records)
        
        # 简化的摘要数据
        detection_types = statistics.get("detection_types", {})
        summary = {
            "total_detections": statistics.get("total_detections", 0),
            "total_targets": statistics.get("total_targets", 0),
            "success_rate": f"{statistics.get('success_rate', 0)}%",
            "average_per_detection": statistics.get("average_targets_per_detection", 0),
            "most_used_type": max(detection_types.items(), key=lambda x: x[1])[0] if detection_types else "无",
            "period_days": days,
            "api_status": "connected"
        }
        
        return {
            "success": True,
            "summary": summary,
            "period": f"最近{days}天",
            "last_updated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取检测摘要失败: {str(e)}")
        # 即使出错也返回基础信息，不抛出异常
        return {
            "success": False,
            "summary": {
                "total_detections": 0,
                "total_targets": 0,
                "error": str(e),
                "api_status": "error"
            },
            "period": f"最近{days}天"
        }

@app.get("/report/test")
async def test_report_dependencies() -> Dict[str, Any]:
    """
    测试报告生成所需的依赖包是否正常
    
    Returns:
        Dict[str, Any]: 依赖检查结果
    """
    dependencies = {
        "reportlab": False,
        "matplotlib": False,
        "statistics": False,
        "collections": False
    }
    
    try:
        import reportlab
        dependencies["reportlab"] = True
        reportlab_version = getattr(reportlab, '__version__', 'unknown')
    except ImportError as e:
        reportlab_version = f"未安装: {str(e)}"
    
    try:
        import matplotlib
        dependencies["matplotlib"] = True
        matplotlib_version = getattr(matplotlib, '__version__', 'unknown')
    except ImportError as e:
        matplotlib_version = f"未安装: {str(e)}"
    
    try:
        import statistics
        dependencies["statistics"] = True
        statistics_version = "内置模块"
    except ImportError as e:
        statistics_version = f"未安装: {str(e)}"
    
    try:
        from collections import Counter
        dependencies["collections"] = True
        collections_version = "内置模块"
    except ImportError as e:
        collections_version = f"未安装: {str(e)}"
    
    all_ready = all(dependencies.values())
    
    return {
        "ready": all_ready,
        "dependencies": dependencies,
        "versions": {
            "reportlab": reportlab_version,
            "matplotlib": matplotlib_version,
            "statistics": statistics_version,
            "collections": collections_version
        },
        "message": "所有依赖已准备就绪" if all_ready else "部分依赖缺失，请安装缺失的包"
    }

@app.get("/report/debug-records")
async def debug_detection_records(current_user_id: int = Depends(verify_token)) -> Dict[str, Any]:
    """
    调试检测记录获取功能
    
    Returns:
        Dict[str, Any]: 调试信息
    """
    debug_info = {
        "user_id": current_user_id,
        "flask_api_url": FLASK_API_BASE_URL,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # 1. 测试Flask API健康状态
        print(f"1. 测试Flask API健康状态...")
        flask_health_response = requests.get(f"{FLASK_API_BASE_URL}/health", timeout=5)
        debug_info["flask_health"] = {
            "status_code": flask_health_response.status_code,
            "response": flask_health_response.json() if flask_health_response.status_code == 200 else flask_health_response.text
        }
        
        # 2. 直接测试检测记录API
        print(f"2. 测试检测记录API...")
        records = await get_user_detection_records(
            user_id=current_user_id,
            limit=20,
            start_date=None,
            end_date=None
        )
        
        debug_info["records_result"] = {
            "success": records is not None,
            "count": len(records) if records else 0,
            "records": records[:5] if records else []  # 只返回前5条用于调试
        }
        
        # 3. 测试Flask API的用户统计
        print(f"3. 测试用户统计API...")
        try:
            flask_token = build_flask_access_token(current_user_id)
            
            headers = {"Authorization": f"Bearer {flask_token}"}
            stats_response = requests.get(f"{FLASK_API_BASE_URL}/user/stats", headers=headers, timeout=5)
            debug_info["user_stats"] = {
                "status_code": stats_response.status_code,
                "response": stats_response.json() if stats_response.status_code == 200 else stats_response.text
            }
        except Exception as e:
            debug_info["user_stats"] = {"error": str(e)}
        
        # 4. 测试直接API调用
        print(f"4. 测试直接检测记录API调用...")
        try:
            records_response = requests.get(
                f"{FLASK_API_BASE_URL}/user/detection-records?limit=10",
                headers=headers,
                timeout=5
            )
            debug_info["direct_records_api"] = {
                "status_code": records_response.status_code,
                "response": records_response.json() if records_response.status_code == 200 else records_response.text
            }
        except Exception as e:
            debug_info["direct_records_api"] = {"error": str(e)}
            
        return {
            "success": True,
            "debug_info": debug_info,
            "summary": {
                "flask_api_connected": debug_info.get("flask_health", {}).get("status_code") == 200,
                "records_available": debug_info.get("records_result", {}).get("success", False),
                "records_count": debug_info.get("records_result", {}).get("count", 0),
                "recommendation": "检查上述调试信息以诊断问题"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "debug_info": debug_info
        }

@app.on_event("startup")
async def on_startup() -> None:
    """启动时加载模型"""
    load_model()


def pil_to_numpy_rgb(img: Image.Image) -> np.ndarray:
    if img.mode != 'RGB':
        img = img.convert('RGB')
    return np.array(img)

def pil_img_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def get_lanczos_resample() -> int:
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return Image.LANCZOS


def encode_preview_frames_to_webp(
    frames: List[Image.Image],
    fps: float,
    max_width: int = 640,
    max_frames: int = 48
) -> str:
    if not frames:
        return ""

    sampled_frames = frames
    if len(sampled_frames) > max_frames:
        step = max(1, (len(sampled_frames) + max_frames - 1) // max_frames)
        sampled_frames = sampled_frames[::step][:max_frames]

    resample_filter = get_lanczos_resample()
    resized_frames: List[Image.Image] = []
    for frame in sampled_frames:
        if frame.width > max_width:
            new_height = max(1, int(frame.height * (max_width / frame.width)))
            resized_frames.append(frame.resize((max_width, new_height), resample_filter))
        else:
            resized_frames.append(frame)

    duration_ms = max(80, int(1000 / max(fps, 1.0)))
    buffered = io.BytesIO()
    resized_frames[0].save(
        buffered,
        format="WEBP",
        save_all=True,
        append_images=resized_frames[1:],
        duration=duration_ms,
        loop=0,
        quality=45,
        method=4
    )
    encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/webp;base64,{encoded}"


def draw_detections(image: Image.Image, detections: List[Dict[str, Any]]) -> Image.Image:
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    for det in detections:
        x1, y1, x2, y2 = det['box']
        label = det['label']
        conf = det['confidence']
        color = (255, 0, 0)
        draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=2)
        text = f"{label} {conf:.2f}"
        # Pillow 10+ 移除了 textsize，使用 textbbox 计算文本尺寸；向下兼容旧版本
        try:
            bbox = draw.textbbox((x1, y1), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            # 旧 Pillow 版本回退
            try:
                tw, th = font.getsize(text)  # type: ignore[attr-defined]
            except Exception:
                tw, th = 0, 0
        bg_top = max(0, y1 - th - 4)
        draw.rectangle([(x1, bg_top), (x1 + tw + 4, y1)], fill=color)
        draw.text((x1 + 2, max(0, y1 - th - 2)), text, fill=(255, 255, 255), font=font)
    return image


@app.post("/infer")
async def infer(
    request: Request,
    file: UploadFile = File(...),
    conf_thres: float = Form(0.25),
    iou_thres: float = Form(0.45),
    return_image: bool = Form(True),
    current_user_id: int = Depends(verify_token)
):
    if model_autoshape is None:
        raise HTTPException(status_code=500, detail="模型未加载")

    img_bytes = await file.read()
    pil_img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    np_img = pil_to_numpy_rgb(pil_img)

    # AutoShape 动态设置阈值
    try:
        # 这些属性在 yolov5/yolov9 的 AutoShape 上可用
        setattr(model_autoshape, 'conf', float(conf_thres))
        setattr(model_autoshape, 'iou', float(iou_thres))
    except Exception as e:
        pass

    # AutoShape 直接处理 numpy 图像
    try:
        with torch.no_grad():
            # 确保输入在正确的设备上
            results = model_autoshape(np_img, size=imgsz_default[0])  # type: ignore
            
            # 处理 Detections 对象
            detections = []
            try:
                # 兼容 yolov5/yolov9 风格的 Detections
                for i, pred in enumerate(results.pred):  # type: ignore
                    im0 = results.ims[i] if hasattr(results, 'ims') else np_img  # type: ignore
                    h0, w0 = (im0.shape[0], im0.shape[1]) if isinstance(im0, np.ndarray) else (pil_img.height, pil_img.width)
                    for *xyxy, conf, cls in pred.tolist():
                        x1, y1, x2, y2 = xyxy
                        cls_idx = int(cls)
                        label = model_names[cls_idx] if model_names and 0 <= cls_idx < len(model_names) else str(cls_idx)
                        detections.append({
                            "box": [max(0, int(x1)), max(0, int(y1)), min(w0, int(x2)), min(h0, int(y2))],
                            "confidence": float(conf),
                            "class": cls_idx,
                            "label": label,
                        })
                
                # 如果需要返回标注后的图像
                image_base64 = None
                
                if return_image and detections:
                    # 在原始图像上绘制检测框
                    annotated = draw_detections(pil_img.copy(), detections)
                    
                    # 将图像保存为 JPEG 格式
                    buf = io.BytesIO()
                    annotated.save(buf, format='JPEG', quality=95)
                    img_base64 = base64.b64encode(buf.getvalue()).decode()
                    image_base64 = f"data:image/jpeg;base64,{img_base64}"
                    buf.close()
                elif return_image and not detections:
                    # 没有检测到目标时返回原图
                    image_base64 = pil_img_to_base64(pil_img)
                
                # 构建响应数据
                response_data = {
                    "detections": detections,
                    "success": True,
                    "msg": f"检测到 {len(detections)} 个目标",
                    "image_base64": image_base64
                }
                
                # 保存检测记录到数据库
                auth_header = request.headers.get("Authorization")
                save_success = await save_detection_record(
                    user_id=current_user_id,
                    file_name=file.filename or "unknown.jpg",
                    detection_type=DetectionType.IMAGE,
                    target_count=len(detections),
                    conf_threshold=conf_thres,
                    iou_threshold=iou_thres,
                    auth_token=auth_header
                )
                
                return response_data
                
            except Exception as e:
                print(f"处理检测结果时出错: {str(e)}")
                raise HTTPException(status_code=500, detail=f"处理检测结果时出错: {str(e)}")
            
    except Exception as e:
        print(f"处理图像时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理图像时出错: {str(e)}")

# 视频推理接口
@app.post("/infer_video")
async def infer_video(
    request: Request,
    file: UploadFile = File(...),
    conf_thres: float = Form(0.1),  # 降低默认置信度阈值
    iou_thres: float = Form(0.45),
    max_frames: int = Form(0),  # 0 表示处理全部帧；>0 表示最多处理 N 帧
    frame_stride: int = Form(1),  # 每隔多少帧处理一次，>=1
    current_user_id: int = Depends(verify_token)
):
    if model_autoshape is None:
        return JSONResponse(status_code=500, content={"error": "Model not loaded"})

    # 设置阈值（兼容 AutoShape 属性）
    try:
        setattr(model_autoshape, 'conf', float(conf_thres))
        setattr(model_autoshape, 'iou', float(iou_thres))
    except Exception:
        pass

    video_bytes = await file.read()
    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, "input_video")
        with open(in_path, 'wb') as f:
            f.write(video_bytes)

        cap = cv2.VideoCapture(in_path)
        if not cap.isOpened():
            return JSONResponse(status_code=400, content={"error": "Failed to read video"})

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        processed = 0
        frame_index = 0
        preview_frames: List[Image.Image] = []
        all_detections: List[Dict[str, Any]] = []  # 收集所有检测结果
        total_targets = 0  # 总目标数量
        preview_frame_limit = 48
        requested_frame_stride = max(1, int(frame_stride or 1))
        requested_max_frames = max(0, int(max_frames or 0))

        effective_frame_stride = requested_frame_stride
        effective_max_frames = requested_max_frames
        if effective_max_frames == 0:
            auto_target_frames = 72
            effective_max_frames = auto_target_frames if total_frames <= 0 else min(auto_target_frames, max(1, total_frames))
            if total_frames > effective_max_frames:
                effective_frame_stride = max(
                    effective_frame_stride,
                    (total_frames + effective_max_frames - 1) // effective_max_frames
                )

        print(
            f"视频检测开始: total_frames={total_frames}, "
            f"requested_stride={requested_frame_stride}, requested_max_frames={requested_max_frames}, "
            f"effective_stride={effective_frame_stride}, effective_max_frames={effective_max_frames}"
        )

        try:
            while True:
                if effective_max_frames > 0 and processed >= effective_max_frames:
                    break

                grabbed = cap.grab()
                if not grabbed:
                    break

                if frame_index % effective_frame_stride != 0:
                    frame_index += 1
                    continue

                ret, frame_bgr = cap.retrieve()
                if not ret:
                    frame_index += 1
                    continue

                # BGR -> RGB -> PIL
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)

                # 推理
                np_img = np.array(pil_img)  # RGB
                with torch.no_grad():
                    results = model_autoshape(np_img, size=imgsz_default[0])  # type: ignore

                dets_json: List[Dict[str, Any]] = []
                try:
                    for i, pred in enumerate(results.pred):  # type: ignore
                        im0 = results.ims[i] if hasattr(results, 'ims') else np_img  # type: ignore
                        h0, w0 = (im0.shape[0], im0.shape[1]) if isinstance(im0, np.ndarray) else (pil_img.height, pil_img.width)
                        
                        for *xyxy, conf, cls in pred.tolist():
                            if conf >= conf_thres:  # 添加置信度过滤检查
                                x1, y1, x2, y2 = xyxy
                                cls_idx = int(cls)
                                label = model_names[cls_idx] if model_names and 0 <= cls_idx < len(model_names) else str(cls_idx)
                                detection = {
                                    "box": [max(0, x1), max(0, y1), min(w0, x2), min(h0, y2)],
                                    "confidence": float(conf),
                                    "class": cls_idx,
                                    "label": label,
                                    "frame": frame_index  # 添加帧索引
                                }
                                dets_json.append(detection)
                                all_detections.append(detection)  # 收集到总列表中
                except Exception as e:
                    print(f"处理帧 {frame_index} 时出错: {str(e)}")
                    frame_index += 1
                    continue

                if len(preview_frames) < preview_frame_limit:
                    preview_frames.append(draw_detections(pil_img.copy(), dets_json))

                total_targets += len(dets_json)
                frame_index += 1
                processed += 1

                if processed % 10 == 0:
                    print(f"视频检测进度: 已处理 {processed} 帧，当前总目标数 {total_targets}")
        finally:
            cap.release()
            print(f"视频处理完成: 处理了{processed}帧, 总目标数{total_targets}")

        preview_base64 = ""
        preview_error = None
        if preview_frames:
            try:
                preview_base64 = encode_preview_frames_to_webp(preview_frames, fps)
            except Exception as e:
                preview_error = str(e)
                print(f"生成视频预览时出错: {preview_error}")

        if processed == 0:
            print("视频导出失败：没有可用的帧")
            response_data = {
                "detections": [],
                "success": False,
                "msg": "视频处理失败，没有可用的帧",
                "video_base64": "",
                "fps": fps,
                "width": width,
                "height": height,
                "frames": total_frames,
                "processed_frames": 0,
                "effective_frame_stride": effective_frame_stride,
                "frame_limit": effective_max_frames,
                "preview_frames": 0,
                "detections_count": 0
            }
        else:
            response_data = {
                "detections": all_detections,
                "success": True,
                "msg": f"检测到 {total_targets} 个目标，共分析 {processed} 帧",
                "video_base64": preview_base64,
                "fps": fps,
                "width": width,
                "height": height,
                "frames": total_frames,
                "processed_frames": processed,
                "effective_frame_stride": effective_frame_stride,
                "frame_limit": effective_max_frames,
                "preview_frames": len(preview_frames),
                "detections_count": total_targets
            }
            if preview_error:
                response_data["error"] = f"视频预览生成失败: {preview_error}"

        auth_header = request.headers.get("Authorization")
        save_success = await save_detection_record(
            user_id=current_user_id,
            file_name=file.filename or "unknown.mp4",
            detection_type=DetectionType.VIDEO,
            target_count=total_targets,
            conf_threshold=conf_thres,
            iou_threshold=iou_thres,
            auth_token=auth_header
        )

        if save_success:
            print("视频检测记录保存成功")
        else:
            print("视频检测记录保存失败")

        return response_data


# WebSocket connection manager for real-time detection
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, websocket: WebSocket, message: dict):
        if (
            websocket.client_state != WebSocketState.CONNECTED or
            websocket.application_state != WebSocketState.CONNECTED
        ):
            self.disconnect(websocket)
            return False

        try:
            await websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            if not is_expected_websocket_close_error(e):
                print(f"发送WebSocket消息失败: {e}")
            self.disconnect(websocket)
            return False

# 全局连接管理器
manager = ConnectionManager()


def is_expected_websocket_close_error(exc: Exception) -> bool:
    message = str(exc)
    return any(fragment in message for fragment in [
        'WebSocket is not connected',
        'Need to call "accept" first',
        'Cannot call "send" once a close message has been sent',
    ])


def process_frame_detection(frame_data: bytes, conf_thres: float, iou_thres: float):
    """处理单帧检测的同步函数"""
    try:
        # 解码base64图像
        image_bytes = base64.b64decode(frame_data.split(',')[1])  # 移除data:image/jpeg;base64,前缀
        pil_img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        np_img = pil_to_numpy_rgb(pil_img)
        
        # 设置模型参数
        if model_autoshape:
            try:
                setattr(model_autoshape, 'conf', float(conf_thres))
                setattr(model_autoshape, 'iou', float(iou_thres))
            except Exception:
                pass

            # 进行检测
            with torch.no_grad():
                realtime_infer_size = 512 if torch.cuda.is_available() else 416
                results = model_autoshape(np_img, size=realtime_infer_size)
                
                # 处理检测结果
                detections = []
                for i, pred in enumerate(results.pred):
                    im0 = results.ims[i] if hasattr(results, 'ims') else np_img
                    h0, w0 = (im0.shape[0], im0.shape[1]) if isinstance(im0, np.ndarray) else (pil_img.height, pil_img.width)
                    
                    for *xyxy, conf, cls in pred.tolist():
                        if conf >= conf_thres:
                            x1, y1, x2, y2 = xyxy
                            cls_idx = int(cls)
                            label = model_names[cls_idx] if model_names and 0 <= cls_idx < len(model_names) else str(cls_idx)
                            detections.append({
                                "box": [max(0, int(x1)), max(0, int(y1)), min(w0, int(x2)), min(h0, int(y2))],
                                "confidence": float(conf),
                                "class": cls_idx,
                                "label": label,
                            })
                
                return {
                    "detections": detections,
                    "frame_width": pil_img.width,
                    "frame_height": pil_img.height,
                    "detection_count": len(detections)
                }
    except Exception as e:
        print(f"处理帧检测时出错: {e}")
        return None

async def verify_websocket_token(token: str) -> int:
    """验证WebSocket令牌并返回用户ID"""
    try:
        print(f"WebSocket认证: 收到令牌 {token[:20]}...")
        
        # 尝试直接解析令牌
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get('sub')
            if user_id:
                # 确保用户ID是整数
                user_id_int = int(user_id) if isinstance(user_id, (str, int)) else None
                if user_id_int:
                    print(f"WebSocket认证成功，用户ID: {user_id_int}")
                    return user_id_int
        except Exception as e:
            if "Subject must be a string" not in str(e):
                print(f"JWT标准解码失败: {e}")
            
        # 手动解析令牌
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("无效的JWT格式")
        
        payload_b64 = parts[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        
        user_id = None
        for field in ['sub', 'identity', 'user_id', 'id']:
            if field in payload:
                user_id = payload[field]
                break
                
        if not user_id:
            raise ValueError("未在令牌中找到用户ID")
        
        print(f"WebSocket手动认证成功，用户ID: {user_id}")
        return int(user_id)
        
    except Exception as e:
        print(f"WebSocket认证失败: {e}")
        raise

@app.websocket("/ws/realtime_detect")
async def websocket_realtime_detect(websocket: WebSocket):
    """实时检测WebSocket端点"""
    print("收到WebSocket连接请求")
    
    # 首先接受连接
    await websocket.accept()
    print("WebSocket连接已接受，等待认证")
    
    # 线程池执行器
    executor = ThreadPoolExecutor(max_workers=2)
    user_id = None
    
    try:
        # 等待认证消息
        auth_data = await websocket.receive_text()
        auth_message = json.loads(auth_data)
        
        if auth_message["type"] != "auth":
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "首先需要发送认证信息"
            }))
            await websocket.close()
            return
        
        # 验证token
        token = auth_message.get("token")
        if not token:
            await websocket.send_text(json.dumps({
                "type": "error", 
                "message": "缺少认证token"
            }))
            await websocket.close()
            return
        
        try:
            user_id = await verify_websocket_token(token)
            manager.active_connections.append(websocket)
            print(f"用户{user_id}的WebSocket连接已建立")
            
            await manager.send_message(websocket, {
                "type": "connected",
                "message": "认证成功，WebSocket连接已建立，可以开始发送帧数据"
            })
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"认证失败: {str(e)}"
            }))
            await websocket.close()
            return
        
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "frame":
                # 处理帧数据
                frame_data = message.get("frame_data")
                conf_thres = message.get("conf_thres", 0.25)
                iou_thres = message.get("iou_thres", 0.45)
                
                if not frame_data:
                    await manager.send_message(websocket, {
                        "type": "error",
                        "message": "没有收到帧数据"
                    })
                    continue
                
                # 在线程池中处理检测
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    executor, 
                    process_frame_detection, 
                    frame_data, 
                    conf_thres, 
                    iou_thres
                )
                
                if result:
                    await manager.send_message(websocket, {
                        "type": "detection_result",
                        "data": result
                    })
                else:
                    await manager.send_message(websocket, {
                        "type": "error", 
                        "message": "帧处理失败"
                    })
            
            elif message["type"] == "ping":
                # 心跳检测
                await manager.send_message(websocket, {
                    "type": "pong",
                    "message": "连接正--常"
                })
            
            elif message["type"] == "start_session":
                # 开始检测会话
                await manager.send_message(websocket, {
                    "type": "session_started",
                    "message": "实时检测会话已开始"
                })
            
            elif message["type"] == "end_session":
                # 客户端准备主动关闭连接，这里直接结束循环，避免对已关闭连接回发消息
                break
                
    except WebSocketDisconnect:
        print("WebSocket连接断开")
    except Exception as e:
        if is_expected_websocket_close_error(e):
            print("WebSocket连接已关闭")
        else:
            print(f"WebSocket处理出错: {e}")
            try:
                await manager.send_message(websocket, {
                    "type": "error",
                    "message": f"服务器错误: {str(e)}"
                })
            except Exception:
                pass
    finally:
        manager.disconnect(websocket)
        executor.shutdown(wait=False)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
