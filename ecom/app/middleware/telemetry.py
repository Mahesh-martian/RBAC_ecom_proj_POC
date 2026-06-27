"""
Telemetry and request tracking middleware.
"""

import uuid
import time
import logging
import json
from typing import Callable
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response tracking, correlation IDs, and structured logging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with telemetry.
        """
        # Generate or retrieve correlation ID
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        
        # Start timer
        start_time = time.time()
        
        # Log request
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_present": bool(request.url.query),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent"),
        }
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Add response headers
            response.headers["X-Request-Id"] = request_id
            response.headers["X-Response-Time-Ms"] = str(latency_ms)
            
            # Log response
            log_data.update({
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "event": "request_completed",
            })
            
            # Log at appropriate level based on status code
            if response.status_code >= 500:
                logger.error(json.dumps(log_data))
            elif response.status_code >= 400:
                logger.warning(json.dumps(log_data))
            else:
                logger.info(json.dumps(log_data))
            
            return response
            
        except Exception as e:
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            log_data.update({
                "status_code": 500,
                "latency_ms": latency_ms,
                "error": "internal_error",
                "event": "request_error",
            })
            
            logger.error(json.dumps(log_data), exc_info=True)
            raise
