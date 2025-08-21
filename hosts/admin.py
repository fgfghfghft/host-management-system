from django.contrib import admin
from .models import City, DataCenter, Host, HostStatistics, RequestLog


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(DataCenter)
class DataCenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'city', 'address', 'created_at']
    list_filter = ['city']
    search_fields = ['name', 'code', 'address']
    ordering = ['city', 'name']


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip_address', 'datacenter', 'status', 'last_password_change']
    list_filter = ['status', 'datacenter__city', 'datacenter']
    search_fields = ['name', 'ip_address']
    ordering = ['datacenter', 'name']
    readonly_fields = ['encrypted_root_password', 'last_password_change', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        # 如果是新建主机且没有设置密码，生成随机密码
        if not change and not obj.encrypted_root_password:
            import random
            import string
            password = ''.join(random.choices(
                string.ascii_letters + string.digits + '!@#$%^&*',
                k=12
            ))
            obj.set_root_password(password)
        super().save_model(request, obj, form, change)


@admin.register(HostStatistics)
class HostStatisticsAdmin(admin.ModelAdmin):
    list_display = ['city', 'datacenter', 'total_hosts', 'active_hosts', 'inactive_hosts', 'maintenance_hosts', 'date']
    list_filter = ['city', 'datacenter', 'date']
    ordering = ['-date', 'city', 'datacenter']
    readonly_fields = ['created_at']


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ['method', 'path', 'response_time', 'status_code', 'ip_address', 'created_at']
    list_filter = ['method', 'status_code', 'created_at']
    search_fields = ['path', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
