from fastapi import FastAPI, Request
from datetime import datetime
import os
from starlette.responses import JSONResponse
import json

app = FastAPI()

# Add mock model list
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
    """Verify API key - allow all keys to pass"""
    return True  # Return True directly, allowing all keys


async def simulate_model_response(messages, model: str):
    """Simulate large model reply"""
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
                "content": f"This is a simulated response using {model} to '{last_message}'."
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
    """Get CORS response headers"""
    return {
        "Access-Control-Allow-Origin": "vscode-file://vscode-app",  # Allow VS Code access
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",  # Add GET method
        "Access-Control-Allow-Headers": "*",  # Allow all headers
        "Access-Control-Allow-Private-Network": "true",  # Allow private network access
        "Access-Control-Allow-Credentials": "true",  # Allow credentials
    }


@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    # Create log directory (if it doesn't exist)
    if not os.path.exists("log"):
        os.makedirs("log")
    
    # Get current time as filename
    filename = f"log/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    
    # Get request information
    method = request.method
    path = request.url.path
    full_url = str(request.url)
    client = (request.client.host + ":" + str(request.client.port) 
              if request.client else "Unknown")
    
    # Get request headers
    headers = dict(request.headers)
    
    # Get request body
    body = await request.body()
    body = body.decode() if body else ""
    
    # Get query parameters
    query_params = str(request.query_params)
    
    # Combine all information
    content = f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"Client: {client}\n"
    content += f"Request Method: {method}\n"
    content += f"Request Path: {path}\n"
    content += f"Full URL: {full_url}\n\n"
    content += "Headers:\n"
    for key, value in headers.items():
        content += f"{key}: {value}\n"
    content += f"\nRequest Body:\n{body}\n\n"
    content += f"Query Parameters: {query_params}\n"
    
    # Write information to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Handle OPTIONS requests
    if method == "OPTIONS":
        return JSONResponse(
            content={},
            headers=get_cors_headers(),
            status_code=200
        )

    # Handle model list requests
    if path.endswith("/models") or path.endswith("/v1/models"):
        return JSONResponse(
            content=AVAILABLE_MODELS,
            headers=get_cors_headers()
        )

    # Handle chat completion requests
    if (path.endswith("/chat/completions") or 
            path.endswith("/v1/chat/completions")):
        try:
            request_data = json.loads(body)
            model = request_data.get("model", "gpt-3.5-turbo")
            response_data = await simulate_model_response(
                request_data.get("messages", []), model
            )
            
            with open(filename, "a", encoding="utf-8") as f:
                f.write(
                    f"\nSimulated Response:\n"
                    f"{json.dumps(response_data, ensure_ascii=False, indent=2)}\n"
                )
            
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

    # Handle other requests
    response = await call_next(request)
    
    # Record response status code
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\nResponse Status Code: {response.status_code}\n")

    # Add CORS headers to all responses
    for key, value in get_cors_headers().items():
        response.headers[key] = value
    
    return response


# Explicitly handle v1 path
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
        response_data = await simulate_model_response(
            request_data.get("messages", []), model
        )
        return JSONResponse(content=response_data, headers=get_cors_headers())
    except Exception as e:
        error_response = {"error": str(e)}
        return JSONResponse(
            content=error_response,
            status_code=400,
            headers=get_cors_headers()
        )


# Capture requests for all paths
@app.api_route("/{path:path}", methods=[
    "GET", "POST", "PUT", "DELETE", "HEAD", "PATCH", "OPTIONS"
])
async def catch_all(request: Request, path: str):
    return {"message": "Request logged", "path": path}


# Add model list interface
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