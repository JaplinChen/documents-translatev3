import json
import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())

        # 標註 request 狀態以便日誌追蹤
        request.state.request_id = request_id

        # 記錄請求資訊
        log_dict = {
            "event": "request_received",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
        }
        logging.info(json.dumps(log_dict))

        try:
            response = await call_next(request)

            process_time = time.perf_counter() - start_time
            log_dict = {
                "event": "request_finished",
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
            }
            logging.info(json.dumps(log_dict))

            # 將 request_id 注入回應標頭，方便除錯
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            process_time = time.perf_counter() - start_time
            log_dict = {
                "event": "request_failed",
                "request_id": request_id,
                "error": str(e),
                "process_time_ms": round(process_time * 1000, 2),
            }
            logging.error(json.dumps(log_dict))
            raise
