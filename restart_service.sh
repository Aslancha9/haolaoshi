#!/bin/bash

# 重启服务脚本
echo "重启推荐系统服务..."

# 停止现有进程
echo "停止现有进程..."
pkill -f "python manage.py runserver"
sleep 2

# 在多个端口启动Django服务器
echo "启动Django服务器..."
# 8000端口
python manage.py runserver 0.0.0.0:8000 > django_8000.log 2>&1 &
echo $! > django_8000.pid

# 8080端口 
python manage.py runserver 0.0.0.0:8080 > django_8080.log 2>&1 &
echo $! > django_8080.pid

# 等待服务器启动
echo "等待服务器启动..."
sleep 5

# 检查服务是否正常
echo "检查服务状态..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "端口8000服务正常"
else
    echo "端口8000服务异常"
fi

if curl -s http://localhost:8080/ > /dev/null; then
    echo "端口8080服务正常"
else
    echo "端口8080服务异常"
fi

echo "服务重启完成"
echo "请使用之前的访问链接访问系统"