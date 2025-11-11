#!/usr/bin/env python3
"""
Insurance Bot API Server - REST API đơn giản với Flask cho frontend app
"""

import os
import sys
import asyncio
import json
import time
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from typing import Optional
from functools import wraps
import logging

# Import bot
sys.path.append('..')
from insurance_bot_minirag import InsuranceBotMiniRAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
import configparser
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'insurance_config.ini')
config.read(config_path)

# Load config to environment variables
for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

# Server configuration
API_HOST = os.environ.get('API_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('API_PORT', 8001))

# API Authentication
API_SECRET_KEY = os.environ.get('API_SECRET_KEY', 'insurance-bot-secret-key-2024')
REQUIRE_API_KEY = os.environ.get('REQUIRE_API_KEY', 'true').lower() == 'true'

# Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Authentication decorator
def require_api_key(f):
    """Decorator to require API key authentication like OpenAI API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if REQUIRE_API_KEY:
            auth_header = request.headers.get('Authorization')
            api_key = request.headers.get('X-API-Key')  # Alternative header

            if not auth_header and not api_key:
                return jsonify({
                    "error": {
                        "message": "Missing API key. Please provide your API key in the Authorization header (Bearer token) or X-API-Key header.",
                        "type": "authentication_error",
                        "code": "missing_api_key"
                    }
                }), 401

            # Check Bearer token format
            if auth_header:
                if not auth_header.startswith('Bearer '):
                    return jsonify({
                        "error": {
                            "message": "Invalid Authorization header format. Use 'Bearer YOUR_API_KEY' format.",
                            "type": "authentication_error",
                            "code": "invalid_auth_format"
                        }
                    }), 401

                provided_key = auth_header.replace('Bearer ', '', 1)
            else:
                provided_key = api_key

            # Validate API key
            if provided_key != API_SECRET_KEY:
                return jsonify({
                    "error": {
                        "message": "Invalid API key provided.",
                        "type": "authentication_error",
                        "code": "invalid_api_key"
                    }
                }), 401

        return f(*args, **kwargs)
    return decorated_function

# Swagger UI Configuration
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/api/spec'  # Our API url (can of course be a local resource)

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Insurance Bot API"
    },
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Global bot instance
bot: Optional[InsuranceBotMiniRAG] = None

# OpenAPI Specification
OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Insurance Bot API",
        "description": "REST API cho chatbot bảo hiểm FISS sử dụng MiniRAG framework",
        "version": "1.0.0",
        "contact": {
            "name": "FISS Insurance Team"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8001",
            "description": "Development server"
        }
    ],
    "paths": {
        "/health": {
            "get": {
                "summary": "Health Check",
                "description": "Kiểm tra trạng thái của API server và bot",
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
                "summary": "Chat với Bot",
                "description": "Gửi tin nhắn để chat với bot bảo hiểm",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ChatRequest"
                            },
                            "example": {
                                "message": "Bảo hiểm xe máy là gì?",
                                "session_id": "optional_session_id"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Chat response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ChatResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request - missing message",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "503": {
                        "description": "Bot not initialized",
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
        },
        "/": {
            "get": {
                "summary": "API Info",
                "description": "Thông tin về API và các endpoints có sẵn",
                "responses": {
                    "200": {
                        "description": "API information",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/APIInfo"
                                }
                            }
                        }
                    }
                },
                "tags": ["Info"]
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
                        "example": "Bảo hiểm xe máy là loại hình bảo hiểm..."
                    },
                    "timestamp": {
                        "type": "number",
                        "example": 1731316800.123
                    },
                    "session_id": {
                        "type": "string",
                        "example": "session_123"
                    },
                    "processing_time": {
                        "type": "number",
                        "description": "Thời gian xử lý (giây)",
                        "example": 35.67
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
            },
            "APIInfo": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Insurance Bot API"
                    },
                    "version": {
                        "type": "string",
                        "example": "1.0.0"
                    },
                    "endpoints": {
                        "type": "object",
                        "properties": {
                            "GET /health": {
                                "type": "string",
                                "example": "Health check"
                            },
                            "POST /chat": {
                                "type": "string",
                                "example": "Chat with bot"
                            }
                        }
                    }
                }
            }
        },
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API Key for authentication (can also use Authorization: Bearer YOUR_API_KEY)"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "description": "Bearer token authentication (Authorization: Bearer YOUR_API_KEY)"
            }
        },
        "security": [
            {
                "ApiKeyAuth": [],
                "BearerAuth": []
            }
        ]
    },
    "tags": [
        {
            "name": "Health",
            "description": "Endpoints kiểm tra trạng thái"
        },
        {
            "name": "Chat",
            "description": "Endpoints chat với bot"
        },
        {
            "name": "Info",
            "description": "Thông tin API"
        }
    ]
}

def init_bot():
    """Initialize bot synchronously"""
    global bot
    try:
        logger.info("🚀 Initializing Insurance Bot...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot = InsuranceBotMiniRAG()
        logger.info("✅ Insurance Bot ready!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        return False

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
        "bot_ready": bot is not None,
        "version": "1.0.0"
    })

@app.route("/chat", methods=["POST"])
@require_api_key
def chat_endpoint():
    """Main chat endpoint"""
    if not bot:
        return jsonify({"error": "Bot not initialized"}), 503

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field"}), 400

        message = data['message']
        session_id = data.get('session_id')

        start_time = time.time()

        # Process message asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(bot.chat(message))

        processing_time = time.time() - start_time

        return jsonify({
            "response": response,
            "timestamp": time.time(),
            "session_id": session_id,
            "processing_time": processing_time
        })

    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/", methods=["GET"])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Insurance Bot API",
        "version": "1.0.0",
        "swagger_ui": f"http://localhost:8001{SWAGGER_URL}",
        "api_spec": f"http://localhost:8001{API_URL}",
        "endpoints": {
            "GET /health": "Health check",
            "POST /chat": "Chat with bot",
            "GET /api/docs": "Swagger UI documentation",
            "GET /api/spec": "OpenAPI specification"
        }
    })

if __name__ == "__main__":
    # Initialize bot
    if init_bot():
        logger.info(f"🚀 Starting server on {API_HOST}:{API_PORT}")
        logger.info(f"📚 Swagger UI: http://localhost:{API_PORT}/api/docs")
        logger.info(f"🔗 API Spec: http://localhost:{API_PORT}/api/spec")
        # Run server
        app.run(
            host=API_HOST,
            port=API_PORT,
            debug=False,
            threaded=True
        )
    else:
        logger.error("❌ Cannot start server - bot initialization failed")
        sys.exit(1)
