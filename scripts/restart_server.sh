#!/bin/bash

# 停止所有现有的Django进程
echo "正在停止现有Django进程..."
pkill -f "python manage.py runserver"
sleep 2

# 确保静态文件目录存在
echo "检查静态文件目录..."
mkdir -p static/images/schools/cqtbi

# 测试数据库连接
echo "测试数据库连接..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'haolaoshi_django.settings')
django.setup()
from django.db import connections
connections['default'].ensure_connection()
print('数据库连接正常')
" || { echo "数据库连接失败"; exit 1; }

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput || echo "无法收集静态文件"

# 使用调试模式启动Django服务器
echo "启动Django服务器..."
python manage.py runserver 0.0.0.0:8000 --nothreading --noreload > django_server.log 2>&1 &
SERVER_PID=$!
echo "服务器进程ID: $SERVER_PID"
echo $SERVER_PID > server.pid

# 等待服务器启动
echo "等待服务器启动..."
sleep 5

# 检查服务器是否正常运行
curl -s http://localhost:8000/ > /dev/null
if [ $? -eq 0 ]; then
    echo "服务器已成功启动，可以访问以下地址："
    echo "本地访问: http://localhost:8000/"
    PUBLIC_IP=$(curl -s ifconfig.me)
    echo "公网访问: http://$PUBLIC_IP:8000/"
else
    echo "服务器可能未正常启动，请检查日志："
    cat django_server.log
fi

# 显示日志的最后几行
echo "服务器日志的最后几行："
tail -10 django_server.log