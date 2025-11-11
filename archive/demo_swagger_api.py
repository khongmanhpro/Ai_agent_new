#!/usr/bin/env python3
"""
Demo API Server - Chỉ để demo Swagger UI, không cần MiniRAG
"""

import os
import sys
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import configparser

# Load configuration
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config', 'insurance_config.ini')
config.read(config_path)

# Load config to environment variables
if 'DEFAULT' in config:
    for key in config['DEFAULT']:
        os.environ[key.upper()] = str(config['DEFAULT'][key])

# Server configuration
API_HOST = os.environ.get('API_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('API_PORT', 8001))

# Flask app
app = Flask(__name__)
CORS(app)

# Swagger UI Configuration
SWAGGER_URL = '/api/docs'
API_URL = '/api/spec'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Insurance Bot API Demo"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# OpenAPI Specification
OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Insurance Bot API Demo",
        "description": "Demo API cho chatbot bảo hiểm - không cần MiniRAG",
        "version": "1.0.0",
        "contact": {
            "name": "FISS Insurance Team"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8001",
            "description": "Demo server"
        }
    ],
    "paths": {
        "/health": {
            "get": {
                "summary": "Health Check",
                "description": "Kiểm tra trạng thái API server",
                "responses": {
                    "200": {
                        "description": "API healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HealthResponse"
                                }
                            }
                        }
                    }
                },
                "tags": ["Health"]
            }
        },
        "/chat": {
            "post": {
                "summary": "Chat với Bot (Demo)",
                "description": "Demo endpoint chat với bot - trả về response mẫu",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ChatRequest"
                            },
                            "example": {
                                "message": "Bảo hiểm xe máy là gì?",
                                "session_id": "demo_session"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Demo chat response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ChatResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                },
                "tags": ["Chat"]
            }
        }
    },
    "components": {
        "schemas": {
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "example": "healthy"
                    },
                    "timestamp": {
                        "type": "number",
                        "example": 1731316800.123
                    },
                    "bot_ready": {
                        "type": "boolean",
                        "example": True
                    },
                    "version": {
                        "type": "string",
                        "example": "1.0.0"
                    }
                }
            },
            "ChatRequest": {
                "type": "object",
                "required": ["message"],
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Tin nhắn cần chat với bot",
                        "example": "Bảo hiểm xe máy là gì?"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID (tùy chọn)",
                        "example": "session_123"
                    }
                }
            },
            "ChatResponse": {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": "Phản hồi từ bot",
                        "example": "Đây là demo response. Bảo hiểm xe máy là loại hình bảo hiểm..."
                    },
                    "timestamp": {
                        "type": "number",
                        "example": 1731316800.123
                    },
                    "session_id": {
                        "type": "string",
                        "example": "demo_session"
                    },
                    "processing_time": {
                        "type": "number",
                        "description": "Thời gian xử lý (giây)",
                        "example": 0.5
                    }
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "Thông báo lỗi",
                        "example": "Missing 'message' field"
                    }
                }
            }
        }
    },
    "tags": [
        {
            "name": "Health",
            "description": "Endpoints kiểm tra trạng thái"
        },
        {
            "name": "Chat",
            "description": "Endpoints chat với bot"
        }
    ]
}

# Demo responses
DEMO_RESPONSES = [
    "Bảo hiểm xe máy là loại hình bảo hiểm bắt buộc theo quy định của pháp luật Việt Nam. Mục đích chính là bảo vệ quyền lợi của người thứ ba bị thiệt hại do tai nạn giao thông.",
    "Theo quy định tại Nghị định 03/2021/NĐ-CP, chủ xe cơ giới phải mua bảo hiểm trách nhiệm dân sự bắt buộc trước khi lưu hành phương tiện.",
    "Bảo hiểm du lịch toàn cầu thường bao gồm các rủi ro như: tai nạn, bệnh tật, mất hành lý, hủy chuyến, và hỗ trợ khẩn cấp 24/7.",
    "Quy tắc bảo hiểm nhà tù nhân thường áp dụng cho các rủi ro như cháy, nổ, lũ lụt, động đất và các thiên tai khác.",
    "Bảo hiểm tai nạn con người thường được sử dụng cho nhân viên, lao động hoặc người tham gia các hoạt động có nguy cơ cao."
]

@app.route("/api/spec", methods=["GET"])
def api_spec():
    """OpenAPI specification endpoint"""
    return jsonify(OPENAPI_SPEC)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "bot_ready": True,
        "version": "1.0.0",
        "demo_mode": True
    })

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Demo chat endpoint"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    message = data['message']
    session_id = data.get('session_id', 'demo_session')

    # Simulate processing time
    import random
    import time as time_module
    processing_time = random.uniform(0.3, 1.5)

    # Get demo response
    response = random.choice(DEMO_RESPONSES)

    return jsonify({
        "response": f"[DEMO MODE] {response}",
        "timestamp": time.time(),
        "session_id": session_id,
        "processing_time": processing_time,
        "note": "Đây là demo response. Để sử dụng bot thật, chạy: python core/insurance_api_simple.py"
    })

@app.route("/", methods=["GET"])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Insurance Bot API Demo",
        "version": "1.0.0",
        "demo_mode": True,
        "swagger_ui": f"http://localhost:8001{SWAGGER_URL}",
        "api_spec": f"http://localhost:8001{API_URL}",
        "endpoints": {
            "GET /health": "Health check",
            "POST /chat": "Chat with bot (demo)"
        },
        "note": "Đây là demo API. Để chạy bot thật với MiniRAG, sử dụng: python core/insurance_api_simple.py"
    })

if __name__ == "__main__":
    print("🚀 Insurance Bot API Demo Server")
    print("=" * 50)
    print(f"📍 Server sẽ chạy tại: http://localhost:{API_PORT}")
    print(f"📚 Swagger UI: http://localhost:{API_PORT}{SWAGGER_URL}")
    print("⚠️  Đây là DEMO MODE - không cần MiniRAG/OpenAI")
    print("🛑 Nhấn Ctrl+C để dừng server")
    print()

    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=False,
        threaded=True
    )
