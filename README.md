# 主机管理系统

一个基于Django + Celery的企业内部主机管理系统，用于管理主机、城市、机房等信息。

## 功能特性

- ✅ 主机、城市、机房的增删改查管理
- ✅ 主机ping可达性探测API
- ✅ 主机root密码加密存储和自动更新
- ✅ 定时任务：每8小时自动修改主机密码
- ✅ 定时任务：每天00:00生成主机统计数据
- ✅ 请求耗时统计中间件
- ✅ RESTful API接口
- ✅ Django管理后台

## 技术栈

- **后端框架**: Django 5.2.5
- **API框架**: Django REST Framework 3.16.1
- **任务队列**: Celery 5.5.3
- **消息代理**: Redis 6.4.0
- **数据库**: SQLite (可替换为MySQL/PostgreSQL)
- **密码加密**: cryptography 45.0.6

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install django celery redis cryptography djangorestframework
```

### 2. 启动Redis服务

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# 或者使用Docker
docker run -d -p 6379:6379 redis:latest
```

### 3. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级用户

```bash
python manage.py createsuperuser
```

### 5. 初始化测试数据

```bash
python manage.py init_data
```

### 6. 启动服务

```bash
# 启动Django开发服务器
python manage.py runserver

# 启动Celery Worker (新终端)
celery -A host_management worker -l info

# 启动Celery Beat (新终端)
celery -A host_management beat -l info
```

## API接口

### 基础URL
- API文档: `http://localhost:8000/api/`
- 管理后台: `http://localhost:8000/admin/`

### 主要接口

#### 城市管理
- `GET /api/cities/` - 获取城市列表
- `POST /api/cities/` - 创建城市
- `GET /api/cities/{id}/` - 获取城市详情
- `PUT /api/cities/{id}/` - 更新城市
- `DELETE /api/cities/{id}/` - 删除城市

#### 机房管理
- `GET /api/datacenters/` - 获取机房列表
- `POST /api/datacenters/` - 创建机房
- `GET /api/datacenters/{id}/` - 获取机房详情
- `PUT /api/datacenters/{id}/` - 更新机房
- `DELETE /api/datacenters/{id}/` - 删除机房

#### 主机管理
- `GET /api/hosts/` - 获取主机列表
- `POST /api/hosts/` - 创建主机
- `GET /api/hosts/{id}/` - 获取主机详情
- `PUT /api/hosts/{id}/` - 更新主机
- `DELETE /api/hosts/{id}/` - 删除主机
- `POST /api/hosts/{id}/ping/` - 探测主机可达性

#### 统计数据
- `GET /api/statistics/` - 获取主机统计数据
- 支持过滤参数: `city_id`, `datacenter_id`, `date`

#### 请求日志
- `GET /api/logs/` - 获取请求日志
- 支持过滤参数: `path`, `method`, `status_code`

## 定时任务

### 密码更新任务
- **频率**: 每8小时执行一次
- **功能**: 为所有主机生成新的随机root密码并加密存储

### 统计任务
- **频率**: 每天00:00执行
- **功能**: 按城市和机房维度统计主机数量

### 主机监控任务
- **频率**: 每小时执行一次
- **功能**: 批量ping所有主机检查可达性

## 数据模型

### City (城市)
- `name`: 城市名称
- `code`: 城市代码
- `created_at`: 创建时间
- `updated_at`: 更新时间

### DataCenter (机房)
- `name`: 机房名称
- `code`: 机房代码
- `city`: 所属城市 (外键)
- `address`: 机房地址
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Host (主机)
- `name`: 主机名称
- `ip_address`: IP地址
- `datacenter`: 所属机房 (外键)
- `status`: 状态 (运行中/已停止/维护中)
- `encrypted_root_password`: 加密的root密码
- `last_password_change`: 密码最后修改时间
- `created_at`: 创建时间
- `updated_at`: 更新时间

### HostStatistics (主机统计)
- `city`: 城市 (外键)
- `datacenter`: 机房 (外键)
- `total_hosts`: 主机总数
- `active_hosts`: 运行中主机数
- `inactive_hosts`: 已停止主机数
- `maintenance_hosts`: 维护中主机数
- `date`: 统计日期
- `created_at`: 创建时间

### RequestLog (请求日志)
- `path`: 请求路径
- `method`: 请求方法
- `response_time`: 响应时间(毫秒)
- `status_code`: 状态码
- `user_agent`: 用户代理
- `ip_address`: IP地址
- `created_at`: 请求时间

## 安全特性

- 主机密码使用Fernet对称加密存储
- 密码字段在API中为只读，防止泄露
- 请求日志记录所有API访问
- 支持IP地址过滤和用户代理记录

## 开发说明

### 添加新的定时任务
1. 在 `hosts/tasks.py` 中定义任务函数
2. 在 `host_management/celery.py` 中配置调度

### 扩展数据模型
1. 修改 `hosts/models.py`
2. 运行 `python manage.py makemigrations`
3. 运行 `python manage.py migrate`

### 自定义中间件
1. 在 `hosts/middleware.py` 中添加中间件类
2. 在 `settings.py` 的 `MIDDLEWARE` 中注册

## 部署建议

### 生产环境配置
- 使用MySQL或PostgreSQL替代SQLite
- 配置Redis集群
- 使用Nginx + Gunicorn部署Django
- 配置SSL证书
- 设置防火墙规则

### 监控建议
- 监控Celery任务执行状态
- 监控Redis连接状态
- 监控数据库性能
- 设置日志轮转

## 许可证

MIT License 