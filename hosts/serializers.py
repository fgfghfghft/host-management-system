from rest_framework import serializers
from .models import City, DataCenter, Host, HostStatistics, RequestLog


class CitySerializer(serializers.ModelSerializer):
    """城市序列化器"""
    
    class Meta:
        model = City
        fields = '__all__'


class DataCenterSerializer(serializers.ModelSerializer):
    """机房序列化器"""
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    class Meta:
        model = DataCenter
        fields = '__all__'


class HostSerializer(serializers.ModelSerializer):
    """主机序列化器"""
    datacenter_name = serializers.CharField(source='datacenter.name', read_only=True)
    city_name = serializers.CharField(source='datacenter.city.name', read_only=True)
    root_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Host
        fields = '__all__'
        extra_kwargs = {
            'encrypted_root_password': {'read_only': True},
            'last_password_change': {'read_only': True},
        }
    
    def create(self, validated_data):
        root_password = validated_data.pop('root_password', None)
        host = Host.objects.create(**validated_data)
        if root_password:
            host.set_root_password(root_password)
        return host
    
    def update(self, instance, validated_data):
        root_password = validated_data.pop('root_password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if root_password:
            instance.set_root_password(root_password)
        instance.save()
        return instance


class HostStatisticsSerializer(serializers.ModelSerializer):
    """主机统计序列化器"""
    city_name = serializers.CharField(source='city.name', read_only=True)
    datacenter_name = serializers.CharField(source='datacenter.name', read_only=True)
    
    class Meta:
        model = HostStatistics
        fields = '__all__'


class RequestLogSerializer(serializers.ModelSerializer):
    """请求日志序列化器"""
    
    class Meta:
        model = RequestLog
        fields = '__all__'


class PingResponseSerializer(serializers.Serializer):
    """Ping响应序列化器"""
    ip_address = serializers.CharField()
    is_reachable = serializers.BooleanField()
    response_time = serializers.FloatField(required=False)
    error_message = serializers.CharField(required=False) 