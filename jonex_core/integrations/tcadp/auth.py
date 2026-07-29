#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
TCADP 平台认证签名模块

实现 TCADP API 签名和验证功能：
1. 请求签名生成（HMAC-SHA256）
2. 响应签名生成
3. Webhook 回调签名验证
"""

import hmac
import hashlib
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import InvalidParameterError

logger = get_logger("tcadp.auth")


class TCADPAuth:
    """TCADP 认证签名类"""

    def __init__(self, api_key: Optional[str] = None, webhook_secret: Optional[str] = None):
        """
        初始化认证客户端

        Args:
            api_key: TCADP API 密钥（默认从配置读取）
            webhook_secret: TCADP Webhook 签名密钥（默认从配置读取）
        """
        config = get_config()
        self.api_key = api_key or config.TCADP_API_KEY or ""
        self.webhook_secret = webhook_secret or config.TCADP_WEBHOOK_SECRET or ""

    def generate_signature(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
    ) -> str:
        """
        生成 API 请求签名

        签名算法:
            1. 拼接请求方法 + 请求路径 + 时间戳 + 有序查询参数 + JSON Body
            2. 使用 HMAC-SHA256 签名，密钥为 API KEY
            3. 结果转换为十六进制字符串

        Args:
            method: HTTP 请求方法 (GET/POST/PUT/DELETE)
            path: 请求路径 (如 /api/v1/capabilities/register)
            params: 查询参数
            body: 请求体
            timestamp: 时间戳（秒，默认使用当前时间）

        Returns:
            str: 签名字符串
        """
        if not self.api_key:
            logger.warning("未配置 TCADP_API_KEY，使用空签名")
            return ""

        if timestamp is None:
            timestamp = int(time.time())

        # 构建签名内容
        signature_parts = [
            method.upper(),
            path,
            str(timestamp),
        ]

        # 添加查询参数（按 key 排序后拼接）
        if params:
            sorted_params = sorted(params.items(), key=lambda x: x[0])
            query_string = urlencode(sorted_params)
            signature_parts.append(query_string)

        # 添加请求体（JSON 字符串）
        if body:
            body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
            signature_parts.append(body_json)

        # 拼接所有部分
        signature_string = "\n".join(signature_parts)

        # HMAC-SHA256 签名
        signature = hmac.new(
            self.api_key.encode("utf-8"),
            signature_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        logger.debug(f"生成签名: timestamp={timestamp}, signature={signature[:16]}...")
        return signature

    def get_auth_headers(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        获取认证请求头

        Args:
            method: HTTP 请求方法
            path: 请求路径
            params: 查询参数
            body: 请求体

        Returns:
            Dict[str, str]: 请求头字典，包含 X-API-Key, X-Timestamp, X-Signature
        """
        timestamp = int(time.time())
        signature = self.generate_signature(method, path, params, body, timestamp)

        return {
            "X-API-Key": self.api_key,
            "X-Timestamp": str(timestamp),
            "X-Signature": signature,
            "Content-Type": "application/json",
        }

    def verify_webhook_signature(
        self,
        headers: Dict[str, str],
        body: str,
    ) -> bool:
        """
        验证 Webhook 回调签名

        Args:
            headers: Webhook 请求头
            body: Webhook 请求体（原始字符串）

        Returns:
            bool: 签名是否有效
        """
        if not self.webhook_secret:
            logger.warning("未配置 TCADP_WEBHOOK_SECRET，跳过 Webhook 签名验证")
            return True

        # 获取请求头中的签名和时间戳
        signature = headers.get("X-Webhook-Signature", "")
        timestamp = headers.get("X-Webhook-Timestamp", "")

        if not signature or not timestamp:
            logger.warning("Webhook 请求缺少签名或时间戳")
            return False

        # 检查时间戳是否在 5 分钟内（防止重放攻击）
        try:
            ts = int(timestamp)
            now = int(time.time())
            if abs(now - ts) > 5 * 60:
                logger.warning(f"Webhook 时间戳超时: {ts} vs {now}")
                return False
        except ValueError:
            logger.warning(f"无效的时间戳: {timestamp}")
            return False

        # 计算期望的签名
        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            f"{timestamp}.{body}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # 安全比较签名（防止时序攻击）
        is_valid = hmac.compare_digest(signature, expected_signature)

        if not is_valid:
            logger.warning(f"Webhook 签名验证失败: {signature[:16]}... vs {expected_signature[:16]}...")

        return is_valid


# 全局单例
_auth_instance: Optional[TCADPAuth] = None


def get_tcadp_auth() -> TCADPAuth:
    """获取 TCADP 认证客户端实例"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = TCADPAuth()
    return _auth_instance
