#!/bin/bash

# 停止所有现有的Django进程
echo "正在停止现有Django进程..."
pkill -f "python manage.py runserver"
sleep 2

# 确保静态文件目录存在
echo "检查静态文件目录..."
mkdir -p static/images/schools/cqtbi

# 在端口8080上启动Django服务器
echo "在端口8080上启动Django服务器..."
python manage.py runserver 0.0.0.0:8080 > django_server_8080.log 2>&1 &
SERVER_PID=$!
echo "服务器进程ID: $SERVER_PID"
echo $SERVER_PID > server_8080.pid

# 等待服务器启动
echo "等待服务器启动..."
sleep 5

# 检查服务器是否正常运行
curl -s http://localhost:8080/ > /dev/null
if [ $? -eq 0 ]; then
    echo "服务器已成功启动，可以访问以下地址："
    echo "本地访问: http://localhost:8080/"
    PUBLIC_IP=$(curl -s ifconfig.me)
    echo "公网访问: http://$PUBLIC_IP:8080/"
    echo "注意: 如果公网IP地址不可访问，可能是云平台限制了端口访问"
else
    echo "服务器可能未正常启动，请检查日志："
    cat django_server_8080.log
fi

# 显示日志的最后几行
echo "服务器日志的最后几行："
tail -10 django_server_8080.log