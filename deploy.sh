#!/bin/bash

# 主机管理系统一键部署脚本
# 使用方法: curl -sSL https://raw.githubusercontent.com/fgfghfghft/host-management-system/master/deploy.sh | bash

set -e  # 遇到错误立即退出

echo "🚀 开始部署主机管理系统..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   print_error "请不要使用root用户运行此脚本"
   exit 1
fi

# 获取当前目录
CURRENT_DIR=$(pwd)
print_message "当前目录: $CURRENT_DIR"

# 检查是否在项目目录中
if [ ! -f "manage.py" ] || [ ! -f "requirements.txt" ]; then
    print_step "检测到不在项目目录中，正在克隆项目..."
    
    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # 克隆项目
    git clone https://github.com/fgfghfghft/host-management-system.git
    cd host-management-system
    
    print_message "项目已克隆到: $(pwd)"
else
    print_message "已在项目目录中: $(pwd)"
fi

# 获取项目目录
PROJECT_DIR=$(pwd)
print_message "项目目录: $PROJECT_DIR"

# 步骤1: 检查系统要求
print_step "1. 检查系统要求..."

# 检查Python版本
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_message "Python版本: $PYTHON_VERSION"
else
    print_error "未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    print_error "未找到pip3，请先安装pip3"
    exit 1
fi

# 步骤2: 安装系统依赖
print_step "2. 安装系统依赖..."

# 检测操作系统并安装依赖
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        print_message "检测到Ubuntu/Debian系统"
        sudo apt-get update
        sudo apt-get install -y python3-venv python3-pip redis-server curl git
        sudo systemctl start redis-server
        sudo systemctl enable redis-server
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        print_message "检测到CentOS/RHEL系统"
        sudo yum install -y python3 python3-pip redis git
        sudo systemctl start redis
        sudo systemctl enable redis
    else
        print_warning "无法自动安装系统依赖，请手动安装Python3、pip3和Redis"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    print_message "检测到macOS系统"
    if command -v brew &> /dev/null; then
        brew install python3 redis git
        brew services start redis
    else
        print_warning "请先安装Homebrew: https://brew.sh/"
        exit 1
    fi
else
    print_warning "不支持的操作系统: $OSTYPE"
    print_warning "请手动安装Python3、pip3和Redis"
fi

# 步骤3: 创建虚拟环境
print_step "3. 创建Python虚拟环境..."

if [ -d "venv" ]; then
    print_warning "虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    print_message "虚拟环境创建成功"
fi

# 激活虚拟环境
source venv/bin/activate

# 步骤4: 安装Python依赖
print_step "4. 安装Python依赖..."

# 升级pip
pip install --upgrade pip

# 安装项目依赖
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_message "Python依赖安装完成"
else
    print_error "未找到requirements.txt文件"
    exit 1
fi

# 步骤5: 数据库迁移
print_step "5. 配置数据库..."

# 创建数据库迁移
python manage.py makemigrations

# 执行数据库迁移
python manage.py migrate

print_message "数据库配置完成"

# 步骤6: 创建超级用户
print_step "6. 创建管理员账号..."

# 检查是否已存在超级用户
if python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).exists())" 2>/dev/null | grep -q "True"; then
    print_warning "超级用户已存在，跳过创建"
else
    print_message "创建管理员账号..."
    
    # 使用非交互方式创建超级用户
    python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'Admin123456')
    print('超级用户创建成功')
else:
    print('超级用户已存在')
"
fi

# 步骤7: 初始化测试数据
print_step "7. 初始化测试数据..."

if command -v python &> /dev/null; then
    python manage.py init_data
    print_message "测试数据初始化完成"
else
    print_warning "跳过测试数据初始化"
fi

# 步骤8: 收集静态文件
print_step "8. 收集静态文件..."

# 创建静态文件目录
mkdir -p static
mkdir -p staticfiles

python manage.py collectstatic --noinput

# 步骤9: 创建启动脚本
print_step "9. 创建启动脚本..."

cat > start_server.sh << 'EOF'
#!/bin/bash
# 主机管理系统启动脚本

echo "🚀 启动主机管理系统..."

# 激活虚拟环境
source venv/bin/activate

# 启动Django服务器
echo "启动Django服务器..."
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# 启动Celery Worker
echo "启动Celery Worker..."
celery -A host_management worker -l info &
CELERY_PID=$!

# 启动Celery Beat
echo "启动Celery Beat..."
celery -A host_management beat -l info &
BEAT_PID=$!

echo "✅ 所有服务已启动!"
echo "📊 管理后台: http://localhost:8000/admin/"
echo "🔗 API接口: http://localhost:8000/api/"
echo "👤 管理员账号: admin / Admin123456"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '正在停止服务...'; kill $DJANGO_PID $CELERY_PID $BEAT_PID; exit" INT
wait
EOF

chmod +x start_server.sh

# 步骤10: 创建停止脚本
cat > stop_server.sh << 'EOF'
#!/bin/bash
# 停止所有服务

echo "🛑 停止主机管理系统..."

# 停止Django进程
pkill -f "python manage.py runserver"

# 停止Celery进程
pkill -f "celery -A host_management worker"
pkill -f "celery -A host_management beat"

echo "✅ 所有服务已停止"
EOF

chmod +x stop_server.sh

# 步骤11: 显示部署完成信息
print_step "10. 部署完成!"

echo ""
echo "🎉 主机管理系统部署完成!"
echo ""
echo "📋 部署信息:"
echo "   项目目录: $PROJECT_DIR"
echo "   虚拟环境: $PROJECT_DIR/venv"
echo "   数据库: SQLite ($PROJECT_DIR/db.sqlite3)"
echo ""
echo "🚀 启动服务:"
echo "   ./start_server.sh"
echo ""
echo "🛑 停止服务:"
echo "   ./stop_server.sh"
echo ""
echo "📊 访问地址:"
echo "   管理后台: http://localhost:8000/admin/"
echo "   API接口: http://localhost:8000/api/"
echo ""
echo "👤 管理员账号:"
echo "   用户名: admin"
echo "   密码: Admin123456"
echo ""
echo "📝 其他命令:"
echo "   激活虚拟环境: source venv/bin/activate"
echo "   查看日志: tail -f celery.log"
echo "   数据库管理: python manage.py shell"
echo ""
echo "🔧 如需修改配置，请编辑 host_management/settings.py"
echo ""

# 询问是否立即启动服务
read -p "是否立即启动服务? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "启动服务..."
    ./start_server.sh
fi 