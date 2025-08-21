from django.core.management.base import BaseCommand
from hosts.models import City, DataCenter, Host
import random
import string


class Command(BaseCommand):
    help = '初始化测试数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化测试数据...')
        
        # 创建城市
        cities_data = [
            {'name': '北京', 'code': 'BJ'},
            {'name': '上海', 'code': 'SH'},
            {'name': '广州', 'code': 'GZ'},
            {'name': '深圳', 'code': 'SZ'},
        ]
        
        cities = []
        for city_data in cities_data:
            city, created = City.objects.get_or_create(
                code=city_data['code'],
                defaults=city_data
            )
            cities.append(city)
            if created:
                self.stdout.write(f'创建城市: {city.name}')
        
        # 创建机房
        datacenters_data = [
            {'name': '北京机房A', 'code': 'BJ-A', 'city': 'BJ'},
            {'name': '北京机房B', 'code': 'BJ-B', 'city': 'BJ'},
            {'name': '上海机房A', 'code': 'SH-A', 'city': 'SH'},
            {'name': '上海机房B', 'code': 'SH-B', 'city': 'SH'},
            {'name': '广州机房A', 'code': 'GZ-A', 'city': 'GZ'},
            {'name': '深圳机房A', 'code': 'SZ-A', 'city': 'SZ'},
        ]
        
        datacenters = []
        for dc_data in datacenters_data:
            city = next(c for c in cities if c.code == dc_data['city'])
            datacenter, created = DataCenter.objects.get_or_create(
                code=dc_data['code'],
                defaults={
                    'name': dc_data['name'],
                    'city': city,
                    'address': f'{city.name}市{dc_data["name"]}地址'
                }
            )
            datacenters.append(datacenter)
            if created:
                self.stdout.write(f'创建机房: {datacenter.name}')
        
        # 创建主机
        host_count = 0
        for datacenter in datacenters:
            # 每个机房创建3-8台主机
            num_hosts = random.randint(3, 8)
            for i in range(num_hosts):
                # 生成随机IP地址
                ip_parts = [
                    random.randint(1, 254),
                    random.randint(1, 254),
                    random.randint(1, 254),
                    random.randint(1, 254)
                ]
                ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{ip_parts[3]}"
                
                # 生成随机密码
                password = ''.join(random.choices(
                    string.ascii_letters + string.digits + '!@#$%^&*',
                    k=12
                ))
                
                host, created = Host.objects.get_or_create(
                    ip_address=ip_address,
                    defaults={
                        'name': f'{datacenter.name}-主机{i+1}',
                        'datacenter': datacenter,
                        'status': random.choice(['active', 'active', 'active', 'inactive', 'maintenance']),
                    }
                )
                
                if created:
                    host.set_root_password(password)
                    host_count += 1
                    self.stdout.write(f'创建主机: {host.name} ({host.ip_address})')
        
        self.stdout.write(
            self.style.SUCCESS(f'初始化完成！创建了 {len(cities)} 个城市，{len(datacenters)} 个机房，{host_count} 台主机')
        ) 