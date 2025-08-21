import subprocess
import platform
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import City, DataCenter, Host, HostStatistics, RequestLog
from .serializers import (
    CitySerializer, DataCenterSerializer, HostSerializer,
    HostStatisticsSerializer, RequestLogSerializer, PingResponseSerializer
)


class CityViewSet(viewsets.ModelViewSet):
    """城市视图集"""
    queryset = City.objects.all()
    serializer_class = CitySerializer


class DataCenterViewSet(viewsets.ModelViewSet):
    """机房视图集"""
    queryset = DataCenter.objects.all()
    serializer_class = DataCenterSerializer


class HostViewSet(viewsets.ModelViewSet):
    """主机视图集"""
    queryset = Host.objects.all()
    serializer_class = HostSerializer
    
    @action(detail=True, methods=['post'])
    def ping(self, request, pk=None):
        """探测主机是否可达"""
        host = self.get_object()
        
        try:
            # 根据操作系统选择ping命令
            if platform.system().lower() == "windows":
                ping_cmd = ["ping", "-n", "1", "-w", "1000", host.ip_address]
            else:
                ping_cmd = ["ping", "-c", "1", "-W", "1", host.ip_address]
            
            # 执行ping命令
            result = subprocess.run(
                ping_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            is_reachable = result.returncode == 0
            response_data = {
                'ip_address': host.ip_address,
                'is_reachable': is_reachable,
            }
            
            if is_reachable:
                # 提取响应时间（如果可能）
                try:
                    if platform.system().lower() == "windows":
                        # Windows ping输出解析
                        for line in result.stdout.split('\n'):
                            if '时间=' in line or 'time=' in line:
                                time_str = line.split('时间=')[-1].split('ms')[0] if '时间=' in line else line.split('time=')[-1].split('ms')[0]
                                response_data['response_time'] = float(time_str)
                                break
                    else:
                        # Linux/Unix ping输出解析
                        for line in result.stdout.split('\n'):
                            if 'time=' in line:
                                time_str = line.split('time=')[-1].split(' ')[0]
                                response_data['response_time'] = float(time_str)
                                break
                except:
                    pass
            else:
                response_data['error_message'] = result.stderr or '主机不可达'
            
            serializer = PingResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
            
        except subprocess.TimeoutExpired:
            return Response({
                'ip_address': host.ip_address,
                'is_reachable': False,
                'error_message': '请求超时'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except Exception as e:
            return Response({
                'ip_address': host.ip_address,
                'is_reachable': False,
                'error_message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HostStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """主机统计视图集（只读）"""
    queryset = HostStatistics.objects.all()
    serializer_class = HostStatisticsSerializer
    
    def get_queryset(self):
        queryset = HostStatistics.objects.all()
        
        # 支持按城市和机房过滤
        city_id = self.request.query_params.get('city_id', None)
        datacenter_id = self.request.query_params.get('datacenter_id', None)
        date = self.request.query_params.get('date', None)
        
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        if datacenter_id:
            queryset = queryset.filter(datacenter_id=datacenter_id)
        if date:
            queryset = queryset.filter(date=date)
            
        return queryset


class RequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    """请求日志视图集（只读）"""
    queryset = RequestLog.objects.all()
    serializer_class = RequestLogSerializer
    
    def get_queryset(self):
        queryset = RequestLog.objects.all()
        
        # 支持按路径、方法、状态码过滤
        path = self.request.query_params.get('path', None)
        method = self.request.query_params.get('method', None)
        status_code = self.request.query_params.get('status_code', None)
        
        if path:
            queryset = queryset.filter(path__icontains=path)
        if method:
            queryset = queryset.filter(method=method.upper())
        if status_code:
            queryset = queryset.filter(status_code=status_code)
            
        return queryset
