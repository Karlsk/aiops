import requests
from functools import wraps
import json, time
from typing import Any
from .logger import TerraLogUtil


# 装饰器：打印请求信息
def log_request_info(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 尝试从 args 或 kwargs 中获取常见参数
        url = args[0] if len(args) > 0 else kwargs.get('url')
        payload = args[1] if len(args) > 1 else kwargs.get('payload')
        headers = args[2] if len(args) > 2 else kwargs.get('headers')

        TerraLogUtil.info(f"Request URL: {url}")
        TerraLogUtil.info(f"Request Payload (JSON): {payload}")
        TerraLogUtil.info(f"Headers: {headers}")
        return func(*args, **kwargs)

    return wrapper


# 装饰器：记录请求耗时
def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        TerraLogUtil.info(f"Request took {duration:.3f} seconds")
        return result

    return wrapper


# 封装的 POST 请求函数
@log_request_info
@measure_time
def do_post(url: str, payload: dict, headers: dict) -> Any:
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
        response.raise_for_status()
        TerraLogUtil.info(f"返回结果：{response.json()}")
        return response
    except requests.exceptions.RequestException as e:
        TerraLogUtil.error("请求失败：%s", e)
        return None
    except Exception as e:
        TerraLogUtil.error("请求失败：%s", e)
        return None


@log_request_info
@measure_time
def do_get(url: str, payload: dict,headers: dict) -> Any:
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        TerraLogUtil.info(f"返回结果：{response.json()}")
        return response
    except Exception as e:
        TerraLogUtil.error("请求失败：%s", e)
        return None


def authorized_request(method, url: str, payload: dict = None, headers: dict = None, get_token_func=None,
                       retry_statuses=(401, 403, 404)):
    global response
    if get_token_func is None:
        raise ValueError("get_token_func must be provided to retrieve access token")

    token = get_token_func()
    headers = headers or {}
    headers["Authorization"] = f"Bearer {token}"
    if method == "GET":
        response = do_get(url, {}, headers)
    elif method == "POST":
        response = do_post(url, payload or {}, headers)
    else:
        raise ValueError("Not implemented")

    if response is None:
        raise ValueError("Connect Controller Error")

    if response.status_code in retry_statuses:
        TerraLogUtil.warning(f"Token may be expired. Refreshing token and retrying...")
        # Refresh token
        token = get_token_func(force_refresh=True)
        headers["Authorization"] = f"Bearer {token}"
        if method == "GET":
            response = do_get(url, {}, headers)
        elif method == "POST":
            response = do_post(url, payload or {}, headers)
        else:
            raise ValueError("Not implemented")

    return response


def authorized_post(url: str, payload: dict = None, headers: dict = None, get_token_func=None,
                    retry_statuses=(401, 403, 404)):
    return authorized_request("POST", url, payload, headers, get_token_func, retry_statuses)


def authorized_get(url: str, headers: dict = None, get_token_func=None,
                   retry_statuses=(401, 403, 404)):
    return authorized_request("GET", url, {}, headers, get_token_func, retry_statuses)
