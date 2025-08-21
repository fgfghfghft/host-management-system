import os
from celery import Celery
from celery.schedules import crontab

# 设置Django默认配置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'host_management.settings')

app = Celery('host_management')

# 使用Django的设置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# Celery Beat 调度配置
app.conf.beat_schedule = {
    'change-passwords-every-8-hours': {
        'task': 'hosts.tasks.change_host_passwords',
        'schedule': crontab(hour='*/8'),  # 每8小时执行一次
    },
    'generate-daily-statistics': {
        'task': 'hosts.tasks.generate_daily_statistics',
        'schedule': crontab(hour=0, minute=0),  # 每天00:00执行
    },
    'ping-hosts-every-hour': {
        'task': 'hosts.tasks.ping_all_hosts',
        'schedule': crontab(minute=0),  # 每小时执行一次
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 