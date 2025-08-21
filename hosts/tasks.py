import random
import string
from celery import shared_task
from django.utils import timezone
from datetime import date
from .models import Host, HostStatistics, City, DataCenter


@shared_task
def change_host_passwords():
    """每8小时修改所有主机的root密码"""
    hosts = Host.objects.all()
    
    for host in hosts:
        # 生成随机密码（12位，包含字母、数字和特殊字符）
        password = ''.join(random.choices(
            string.ascii_letters + string.digits + '!@#$%^&*',
            k=12
        ))
        
        # 设置新密码
        host.set_root_password(password)
        
        print(f"已更新主机 {host.name} ({host.ip_address}) 的密码")


@shared_task
def generate_daily_statistics():
    """每天00:00生成主机统计数据"""
    today = date.today()
    
    # 获取所有城市和机房
    cities = City.objects.all()
    
    for city in cities:
        datacenters = city.datacenters.all()
        
        for datacenter in datacenters:
            # 获取该机房的所有主机
            hosts = datacenter.hosts.all()
            
            # 统计各状态的主机数量
            total_hosts = hosts.count()
            active_hosts = hosts.filter(status='active').count()
            inactive_hosts = hosts.filter(status='inactive').count()
            maintenance_hosts = hosts.filter(status='maintenance').count()
            
            # 创建或更新统计记录
            statistics, created = HostStatistics.objects.get_or_create(
                city=city,
                datacenter=datacenter,
                date=today,
                defaults={
                    'total_hosts': total_hosts,
                    'active_hosts': active_hosts,
                    'inactive_hosts': inactive_hosts,
                    'maintenance_hosts': maintenance_hosts,
                }
            )
            
            if not created:
                # 更新现有记录
                statistics.total_hosts = total_hosts
                statistics.active_hosts = active_hosts
                statistics.inactive_hosts = inactive_hosts
                statistics.maintenance_hosts = maintenance_hosts
                statistics.save()
            
            print(f"已生成 {city.name}-{datacenter.name} 的统计数据: "
                  f"总数={total_hosts}, 运行中={active_hosts}, "
                  f"已停止={inactive_hosts}, 维护中={maintenance_hosts}")


@shared_task
def ping_all_hosts():
    """批量ping所有主机检查可达性"""
    import subprocess
    import platform
    
    hosts = Host.objects.all()
    
    for host in hosts:
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
            
            # 更新主机状态（可选：根据ping结果更新状态）
            if not is_reachable and host.status == 'active':
                host.status = 'inactive'
                host.save()
                print(f"主机 {host.name} ({host.ip_address}) 不可达，状态已更新为已停止")
            elif is_reachable and host.status == 'inactive':
                host.status = 'active'
                host.save()
                print(f"主机 {host.name} ({host.ip_address}) 可达，状态已更新为运行中")
                
        except Exception as e:
            print(f"ping主机 {host.name} ({host.ip_address}) 时出错: {str(e)}") 