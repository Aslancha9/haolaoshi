#!/bin/bash

echo "==============================================="
echo "网络连接测试脚本"
echo "==============================================="

# 检查公网IP
echo "检查公网IP地址..."
PUBLIC_IP=$(curl -s ifconfig.me)
echo "公网IP: $PUBLIC_IP"

# 检查服务器是否正在监听8000端口
echo -e "\n检查服务器端口监听状态..."
nc -z -v localhost 8000 2>&1 || echo "无法使用nc命令检查端口"
python -c "import socket; s=socket.socket(); s.connect(('localhost', 8000)); print('端口8000正在监听'); s.close();" 2>/dev/null || echo "端口8000未监听"

# 检查进程
echo -e "\n检查Django进程..."
ps aux | grep "python manage.py runserver" | grep -v grep

# 尝试在不同端口启动测试服务器
echo -e "\n尝试在其他端口启动测试HTTP服务器..."
(python -m http.server 8888 --bind 0.0.0.0 > /dev/null 2>&1) &
HTTP_PID=$!
sleep 3
kill $HTTP_PID 2>/dev/null
echo "测试HTTP服务器已启动并关闭"

# 测试从本机到公网端口的连接
echo -e "\n测试从本机连接公网端口..."
curl -I http://$PUBLIC_IP:8000/ -m 5 2>/dev/null || echo "无法连接到公网IP的8000端口"

# 打印服务器日志的最后几行
echo -e "\n服务器日志的最后10行:"
tail -10 django_server.log

# 检查是否是虚拟环境或Docker环境
echo -e "\n检查运行环境..."
if [ -f /.dockerenv ]; then
    echo "在Docker容器中运行"
fi

if [ -n "$VIRTUAL_ENV" ]; then
    echo "在Python虚拟环境中运行: $VIRTUAL_ENV"
fi

# 查看云平台信息
echo -e "\n查看云平台信息..."
if [ -f /etc/autodl-platform ]; then
    echo "在AutoDL平台运行"
    cat /etc/autodl-platform
fi

# 提供建议
echo -e "\n====================================================="
echo "问题诊断与解决建议:"
echo "1. 可能是云平台限制了端口访问，尝试更换为常用端口(80/443/8080):"
echo "   python manage.py runserver 0.0.0.0:8080"
echo ""
echo "2. 尝试使用ngrok或cloudflared隧道:"
echo "   ./cloudflared tunnel --url http://localhost:8000"
echo ""  
echo "3. 如果在AutoDL平台，尝试使用SSH隧道:"
echo "   ssh -N -L 8080:localhost:8000 root@$PUBLIC_IP"
echo ""
echo "4. 检查防火墙设置，确保允许端口访问"
echo "======================================================"