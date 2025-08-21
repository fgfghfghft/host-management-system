from django.db import models
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import base64


class City(models.Model):
    """城市模型"""
    name = models.CharField(max_length=100, verbose_name='城市名称')
    code = models.CharField(max_length=20, unique=True, verbose_name='城市代码')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '城市'
        verbose_name_plural = '城市'
        ordering = ['name']

    def __str__(self):
        return self.name


class DataCenter(models.Model):
    """机房模型"""
    name = models.CharField(max_length=100, verbose_name='机房名称')
    code = models.CharField(max_length=20, unique=True, verbose_name='机房代码')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='datacenters', verbose_name='所属城市')
    address = models.TextField(blank=True, verbose_name='机房地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '机房'
        verbose_name_plural = '机房'
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.city.name}-{self.name}"


class Host(models.Model):
    """主机模型"""
    STATUS_CHOICES = [
        ('active', '运行中'),
        ('inactive', '已停止'),
        ('maintenance', '维护中'),
    ]

    name = models.CharField(max_length=100, verbose_name='主机名称')
    ip_address = models.GenericIPAddressField(unique=True, verbose_name='IP地址')
    datacenter = models.ForeignKey(DataCenter, on_delete=models.CASCADE, related_name='hosts', verbose_name='所属机房')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    encrypted_root_password = models.TextField(verbose_name='加密的root密码')
    last_password_change = models.DateTimeField(auto_now_add=True, verbose_name='密码最后修改时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '主机'
        verbose_name_plural = '主机'
        ordering = ['datacenter', 'name']

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    def set_root_password(self, password):
        """加密并设置root密码"""
        fernet = Fernet(settings.ENCRYPTION_KEY)
        encrypted_password = fernet.encrypt(password.encode())
        self.encrypted_root_password = base64.b64encode(encrypted_password).decode()
        self.last_password_change = timezone.now()
        self.save()

    def get_root_password(self):
        """解密获取root密码"""
        fernet = Fernet(settings.ENCRYPTION_KEY)
        encrypted_password = base64.b64decode(self.encrypted_root_password.encode())
        return fernet.decrypt(encrypted_password).decode()


class HostStatistics(models.Model):
    """主机统计模型"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name='城市')
    datacenter = models.ForeignKey(DataCenter, on_delete=models.CASCADE, verbose_name='机房')
    total_hosts = models.IntegerField(default=0, verbose_name='主机总数')
    active_hosts = models.IntegerField(default=0, verbose_name='运行中主机数')
    inactive_hosts = models.IntegerField(default=0, verbose_name='已停止主机数')
    maintenance_hosts = models.IntegerField(default=0, verbose_name='维护中主机数')
    date = models.DateField(verbose_name='统计日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '主机统计'
        verbose_name_plural = '主机统计'
        unique_together = ['city', 'datacenter', 'date']
        ordering = ['-date', 'city', 'datacenter']

    def __str__(self):
        return f"{self.city.name}-{self.datacenter.name} ({self.date})"


class RequestLog(models.Model):
    """请求日志模型"""
    path = models.CharField(max_length=255, verbose_name='请求路径')
    method = models.CharField(max_length=10, verbose_name='请求方法')
    response_time = models.FloatField(verbose_name='响应时间(毫秒)')
    status_code = models.IntegerField(verbose_name='状态码')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='请求时间')

    class Meta:
        verbose_name = '请求日志'
        verbose_name_plural = '请求日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.method} {self.path} - {self.response_time}ms"
