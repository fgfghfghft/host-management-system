import time
from django.utils.deprecation import MiddlewareMixin
from .models import RequestLog


class RequestTimeMiddleware(MiddlewareMixin):
    """请求耗时统计中间件"""
    
    def process_request(self, request):
        """请求开始时的处理"""
        request.start_time = time.time()
    
    def process_response(self, request, response):
        """请求结束时的处理"""
        if hasattr(request, 'start_time'):
            # 计算响应时间（毫秒）
            response_time = (time.time() - request.start_time) * 1000
            
            # 获取客户端IP地址
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
            
            # 记录请求日志
            RequestLog.objects.create(
                path=request.path,
                method=request.method,
                response_time=response_time,
                status_code=response.status_code,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=ip_address
            )
        
        return response 