from fastapi import FastAPI, Request, HTTPException
from datetime import datetime
import os
from starlette.responses import JSONResponse
import json

app = FastAPI()

# 添加模拟的模型列表
AVAILABLE_MODELS = {
    "data": [
        {
            "id": "gpt-4",
            "object": "model",
            "created": 1687882410,
            "owned_by": "openai",
            "permission": [],
            "root": "gpt-4",
            "parent": None
        },
        {
            "id": "gpt-4-turbo",
            "object": "model",
            "created": 1687882410,
            "owned_by": "openai",
            "permission": [],
            "root": "gpt-4",
            "parent": None
        },
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "created": 1687882410,
            "owned_by": "openai",
            "permission": [],
            "root": "gpt-3.5-turbo",
            "parent": None
        },
        {
            "id": "gpt-4o-mini",
            "object": "model",
            "created": 1687882410,
            "owned_by": "openai",
            "permission": [],
            "root": "gpt-4",
            "parent": None
        }
    ],
    "object": "list"
}

def verify_api_key(authorization: str) -> bool:
    """验证API密钥 - 允许所有密钥通过"""
    return True  # 直接返回True，允许所有密钥

async def simulate_model_response(messages, model: str):
    """模拟大模型回复"""
    last_message = messages[-1]["content"] if messages else ""
    return {
        "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": f"这是使用{model}模型对'{last_message}'的模拟回复。"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

def get_cors_headers():
    """获取CORS响应头"""
    return {
        "Access-Control-Allow-Origin": "vscode-file://vscode-app",  # 允许 VS Code 访问
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",  # 添加 GET 方法
        "Access-Control-Allow-Headers": "*",  # 允许所有头部
        "Access-Control-Allow-Private-Network": "true",  # 允许访问私有网络
        "Access-Control-Allow-Credentials": "true",  # 允许携带凭证
    }

@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    # 创建日志目录（如果不存在）
    if not os.path.exists("log"):
        os.makedirs("log")
    
    # 获取当前时间作为文件名
    filename = f"log/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    
    # 获取请求信息
    method = request.method
    path = request.url.path
    full_url = str(request.url)
    client = request.client.host + ":" + str(request.client.port) if request.client else "Unknown"
    
    # 获取请求头
    headers = dict(request.headers)
    
    # 获取请求体
    body = await request.body()
    body = body.decode() if body else ""
    
    # 获取查询参数
    query_params = str(request.query_params)
    
    # 组合所有信息
    content = f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"客户端: {client}\n"
    content += f"请求方法: {method}\n"
    content += f"请求路径: {path}\n"
    content += f"完整URL: {full_url}\n\n"
    content += "请求头:\n"
    for key, value in headers.items():
        content += f"{key}: {value}\n"
    content += f"\n请求体:\n{body}\n\n"
    content += f"查询参数: {query_params}\n"
    
    # 将信息写入文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    # 处理 OPTIONS 请求
    if method == "OPTIONS":
        return JSONResponse(
            content={},
            headers=get_cors_headers(),
            status_code=200
        )

    # 处理模型列表请求
    if path.endswith("/models") or path.endswith("/v1/models"):
        return JSONResponse(
            content=AVAILABLE_MODELS,
            headers=get_cors_headers()
        )

    # 处理聊天完成请求
    if path.endswith("/chat/completions") or path.endswith("/v1/chat/completions"):
        try:
            request_data = json.loads(body)
            model = request_data.get("model", "gpt-3.5-turbo")
            response_data = await simulate_model_response(request_data.get("messages", []), model)
            
            with open(filename, "a", encoding="utf-8") as f:
                f.write(f"\n模拟响应:\n{json.dumps(response_data, ensure_ascii=False, indent=2)}\n")
            
            return JSONResponse(
                content=response_data,
                headers=get_cors_headers()
            )
        except Exception as e:
            error_response = {"error": str(e)}
            return JSONResponse(
                content=error_response,
                status_code=400,
                headers=get_cors_headers()
            )

    # 处理其他请求
    response = await call_next(request)
    
    # 记录响应状态码
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\n响应状态码: {response.status_code}\n")

    # 为所有响应添加 CORS 头
    for key, value in get_cors_headers().items():
        response.headers[key] = value
    
    return response

# 显式处理 v1 路径
@app.options("/v1/chat/completions")
async def options_chat_completions():
    return JSONResponse(content={}, headers=get_cors_headers())

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.body()
    body_str = body.decode()
    try:
        request_data = json.loads(body_str)
        print(request_data)
        model = request_data.get("model", "gpt-3.5-turbo")
        response_data = await simulate_model_response(request_data.get("messages", []), model)
        return JSONResponse(content=response_data, headers=get_cors_headers())
    except Exception as e:
        error_response = {"error": str(e)}
        return JSONResponse(
            content=error_response,
            status_code=400,
            headers=get_cors_headers()
        )

# 捕获所有路径的请求
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH", "OPTIONS"])
async def catch_all(request: Request, path: str):
    return {"message": "请求已记录", "path": path}

# 添加模型列表接口
@app.get("/models")
@app.get("/v1/models")
async def list_models():
    return JSONResponse(
        content=AVAILABLE_MODELS,
        headers=get_cors_headers()
    )

@app.options("/models")
@app.options("/v1/models")
async def options_models():
    return JSONResponse(
        content={},
        headers=get_cors_headers()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 