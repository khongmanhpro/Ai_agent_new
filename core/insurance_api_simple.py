#!/usr/bin/env python3
"""
Insurance Bot API Server - REST API đơn giản với Flask cho frontend app
"""

import os
import sys
import asyncio
import json
import time
from flask import Flask, request, jsonify, abort, Response, stream_with_context
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
API_SECRET_KEY = os.environ.get('API_SECRET_KEY', 'fiss-c61197f847cc4682a91ada560bbd7119')
REQUIRE_API_KEY = os.environ.get('REQUIRE_API_KEY', 'true').lower() == 'true'

# API Authentication settings loaded

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

            # DEBUG: Log all headers and API key
            logger.info(f"🔍 DEBUG AUTH - All headers: {dict(request.headers)}")
            logger.info(f"🔍 DEBUG AUTH - Authorization header: {auth_header}")
            logger.info(f"🔍 DEBUG AUTH - X-API-Key header: {api_key}")
            logger.info(f"🔍 DEBUG AUTH - Expected API_SECRET_KEY: {API_SECRET_KEY}")
            logger.info(f"🔍 DEBUG AUTH - REQUIRE_API_KEY: {REQUIRE_API_KEY}")

            if not auth_header and not api_key:
                logger.warning("❌ AUTH FAILED - Missing both Authorization and X-API-Key headers")
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
                    logger.warning(f"❌ AUTH FAILED - Invalid Authorization format: {auth_header}")
                    return jsonify({
                        "error": {
                            "message": "Invalid Authorization header format. Use 'Bearer YOUR_API_KEY' format.",
                            "type": "authentication_error",
                            "code": "invalid_auth_format"
                        }
                    }), 401

                provided_key = auth_header.replace('Bearer ', '', 1)
                logger.info(f"🔍 DEBUG AUTH - Extracted key from Bearer: {provided_key[:20]}...")
            else:
                provided_key = api_key
                logger.info(f"🔍 DEBUG AUTH - Using X-API-Key: {provided_key[:20] if provided_key else 'None'}...")

            # Validate API key
            logger.info(f"🔍 DEBUG AUTH - Comparing keys:")
            logger.info(f"   Provided: '{provided_key}' (len={len(provided_key) if provided_key else 0})")
            logger.info(f"   Expected: '{API_SECRET_KEY}' (len={len(API_SECRET_KEY)})")
            logger.info(f"   Match: {provided_key == API_SECRET_KEY}")
            
            if provided_key != API_SECRET_KEY:
                logger.warning(f"❌ AUTH FAILED - Key mismatch. Provided: '{provided_key}', Expected: '{API_SECRET_KEY}'")
                return jsonify({
                    "error": {
                        "message": "Invalid API key provided.",
                        "type": "authentication_error",
                        "code": "invalid_api_key"
                    }
                }), 401

            logger.info("✅ AUTH SUCCESS - API key validated")
        return f(*args, **kwargs)
    return decorated_function

# Swagger UI Configuration
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/api/spec'  # Our API url (can of course be a local resource)

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Insurance Bot API",
        'persistAuthorization': True,  # Lưu API key sau khi refresh
        'defaultModelsExpandDepth': 1,
        'defaultModelExpandDepth': 1,
    },
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Custom route to inject auto-auth script into Swagger UI
@app.route("/api/docs/")
def swagger_ui_index():
    """Serve Swagger UI with auto-auth script injection"""
    api_key = API_SECRET_KEY
    try:
        # Get the original Swagger UI HTML from the blueprint
        from flask import make_response, render_template_string
        import urllib.request
        
        # Fetch the Swagger UI HTML
        swagger_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Insurance Bot API - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="/api/docs/swagger-ui.css" />
    <link rel="stylesheet" type="text/css" href="/api/docs/index.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="/api/docs/swagger-ui-bundle.js"></script>
    <script src="/api/docs/swagger-ui-standalone-preset.js"></script>
    <script>
        const apiKey = '{api_key}';
        
        // Swagger UI configuration - Professional setup
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: "/api/spec",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                persistAuthorization: true,
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                docExpansion: "list",
                filter: true,
                showExtensions: true,
                showCommonExtensions: true,
                tryItOutEnabled: true,
                requestInterceptor: function(request) {{
                    // Ensure API key is always sent
                    if (!request.headers.Authorization && !request.headers['X-API-Key']) {{
                        request.headers['X-API-Key'] = apiKey;
                    }}
                    return request;
                }},
                onComplete: function() {{
                    // Auto-set API key when Swagger UI loads
                    if (window.ui && typeof window.ui.preauthorizeApiKey === 'function') {{
                        window.ui.preauthorizeApiKey("BearerAuth", apiKey);
                        window.ui.preauthorizeApiKey("ApiKeyAuth", apiKey);
                        console.log("✅ API Key tự động được set:", apiKey);
                    }}
                }}
            }});
            
            // Store ui instance globally
            window.ui = ui;
            
            // Auto-set API key with retry mechanism
            let attempts = 0;
            const maxAttempts = 10;
            const setApiKeyInterval = setInterval(function() {{
                attempts++;
                if (window.ui && typeof window.ui.preauthorizeApiKey === 'function') {{
                    window.ui.preauthorizeApiKey("BearerAuth", apiKey);
                    window.ui.preauthorizeApiKey("ApiKeyAuth", apiKey);
                    console.log("✅ API Key đã được set tự động");
                    clearInterval(setApiKeyInterval);
                }} else if (attempts >= maxAttempts) {{
                    console.warn("⚠️ Không thể auto-set API key. Vui lòng nhập thủ công vào nút Authorize.");
                    clearInterval(setApiKeyInterval);
                }}
            }}, 300);
        }};
    </script>
</body>
</html>
"""
        response = make_response(swagger_html)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    except Exception as e:
        logger.error(f"Error serving Swagger UI: {e}")
        # Fallback to default Swagger UI
        from flask import redirect
        return redirect('/api/docs/index.html?url=/api/spec')

# Global bot instance
bot: Optional[InsuranceBotMiniRAG] = None

# OpenAPI Specification
OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "FISS Insurance Bot API",
        "description": "REST API chuyên nghiệp cho chatbot bảo hiểm FISS. API này cung cấp khả năng chat với bot thông minh để trả lời các câu hỏi về bảo hiểm.\n\n## Authentication\n\nAPI key bắt buộc phải được cung cấp trong header:\n- **X-API-Key**: `fiss-c61197f847cc4682a91ada560bbd7119`\n- **Hoặc Authorization**: `Bearer fiss-c61197f847cc4682a91ada560bbd7119`\n\n## Quick Start\n\n1. Click nút **Authorize** (🔒) ở góc trên bên phải\n2. Nhập API key vào một trong hai options\n3. Click **Authorize** → **Close**\n4. Test API bằng cách click **Try it out** và **Execute**",
        "version": "1.0.0",
        "contact": {
            "name": "FISS Insurance Team",
            "email": "support@fiss.com"
        },
        "license": {
            "name": "Proprietary"
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
                "description": "Gửi tin nhắn để chat với bot bảo hiểm FISS. API key bắt buộc phải được cung cấp trong header.",
                "security": [
                    {
                        "ApiKeyAuth": []
                    },
                    {
                        "BearerAuth": []
                    }
                ],
                "parameters": [
                    {
                        "name": "x-api-version",
                        "in": "header",
                        "description": "API version (optional)",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "default": "1.0.0"
                        },
                        "example": "1.0.0"
                    }
                ],
                "requestBody": {
                    "required": True,
                    "description": "Request body chứa câu hỏi cần chat với bot",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ChatRequest"
                            },
                            "example": {
                                "message": "Bảo hiểm xe máy là gì?"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Chat response thành công",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ChatResponse"
                                },
                                "example": {
                                    "response": "Bảo hiểm xe máy là loại hình bảo hiểm bắt buộc theo quy định của pháp luật Việt Nam...",
                                    "timestamp": 1731316800.123,
                                    "session_id": "session_123",
                                    "processing_time": 2.5
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized - Thiếu hoặc sai API key",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                },
                                "example": {
                                    "error": {
                                        "message": "Missing API key. Please provide your API key in the Authorization header (Bearer token) or X-API-Key header.",
                                        "type": "authentication_error",
                                        "code": "missing_api_key"
                                    }
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
                        "description": "Câu hỏi hoặc tin nhắn cần chat với bot",
                        "example": "Bảo hiểm xe máy là gì?"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID để duy trì context cuộc hội thoại (tùy chọn)",
                        "example": "session_123"
                    }
                },
                "additionalProperties": False
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
                "description": "API Key cho authentication. Nhập API key của bạn vào đây.",
                "x-default": "fiss-c61197f847cc4682a91ada560bbd7119"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "API Key",
                "description": "Bearer token authentication. Format: Bearer YOUR_API_KEY. Nhập API key của bạn vào đây (không cần gõ 'Bearer')."
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

# Global event loop để reuse (tối ưu performance)
_global_event_loop: Optional[asyncio.AbstractEventLoop] = None

def get_or_create_event_loop():
    """Get or create global event loop để reuse (tối ưu performance)"""
    global _global_event_loop
    if _global_event_loop is None or _global_event_loop.is_closed():
        try:
            # Thử lấy event loop hiện tại
            _global_event_loop = asyncio.get_event_loop()
        except RuntimeError:
            # Nếu không có, tạo mới
            _global_event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_global_event_loop)
    return _global_event_loop

def init_bot():
    """Initialize bot synchronously"""
    global bot
    try:
        logger.info("🚀 Initializing Insurance Bot...")
        loop = get_or_create_event_loop()
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

@app.after_request
def inject_swagger_auth(response):
    """Inject JavaScript to auto-set API key in Swagger UI"""
    api_key = API_SECRET_KEY
    if request.path == '/api/docs/' and response.content_type and 'text/html' in response.content_type:
        try:
            # Decode response data
            if hasattr(response, 'data'):
                html = response.data.decode('utf-8')
                # Inject script before closing body tag
                script = f"""
<script>
(function() {{
    const apiKey = '{api_key}';
    
    // Save to localStorage for persistence
    try {{
        const authData = {{
            BearerAuth: {{ value: apiKey }},
            ApiKeyAuth: {{ value: apiKey }}
        }};
        localStorage.setItem('swagger-ui-auth', JSON.stringify(authData));
        console.log('✅ API Key saved to localStorage');
    }} catch(e) {{
        console.warn('Could not save to localStorage:', e);
    }}
    
    // Auto-set API key when Swagger UI loads
    function setApiKey() {{
        if (window.ui && typeof window.ui.preauthorizeApiKey === 'function') {{
            window.ui.preauthorizeApiKey('BearerAuth', apiKey);
            window.ui.preauthorizeApiKey('ApiKeyAuth', apiKey);
            console.log('✅ API Key auto-set:', apiKey);
            return true;
        }}
        return false;
    }}
    
    // Try multiple times until Swagger UI is ready
    let attempts = 0;
    const maxAttempts = 50;
    const interval = setInterval(function() {{
        attempts++;
        if (setApiKey() || attempts >= maxAttempts) {{
            clearInterval(interval);
        }}
    }}, 200);
    
    // Also try on window load
    window.addEventListener('load', function() {{
        setTimeout(setApiKey, 1000);
    }});
}})();
</script>
"""
                html = html.replace('</body>', script + '</body>')
                response.data = html.encode('utf-8')
        except Exception as e:
            logger.warning(f"Could not inject auth script: {e}")
    return response

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
    """Main chat endpoint - Non-streaming"""
    if not bot:
        return jsonify({"error": "Bot not initialized"}), 503

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field"}), 400

        message = data['message']
        session_id = data.get('session_id')

        start_time = time.time()

        # Process message asynchronously - reuse event loop (tối ưu performance)
        loop = get_or_create_event_loop()
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

@app.route("/chat/stream", methods=["POST"])
@require_api_key
def chat_stream_endpoint():
    """Streaming chat endpoint - Server-Sent Events (SSE)"""
    if not bot:
        return jsonify({"error": "Bot not initialized"}), 503

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field"}), 400

        message = data['message']
        session_id = data.get('session_id')

        def generate():
            """Generator function for Server-Sent Events"""
            loop = get_or_create_event_loop()
            
            # Run async generator in sync context
            async def stream_response():
                full_response = ""
                async for chunk in bot.chat_stream(message):
                    full_response += chunk
                    # Format as SSE
                    yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
                
                # Send final message
                yield f"data: {json.dumps({'chunk': '', 'done': True, 'full_response': full_response, 'session_id': session_id})}\n\n"
            
            # Convert async generator to sync generator
            async_gen = stream_response()
            try:
                while True:
                    try:
                        chunk = loop.run_until_complete(async_gen.__anext__())
                        yield chunk
                    except StopAsyncIteration:
                        break
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',  # Disable buffering in nginx
                'Connection': 'keep-alive',
            }
        )

    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/", methods=["GET"])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Insurance Bot API",
        "version": "1.0.0",
        "chat_ui": "http://localhost:3000 (Node.js Chat UI)",
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
