#!/bin/bash

# 全面解决方案脚本
echo "=========================================="
echo "         考研推荐系统启动脚本             "
echo "=========================================="

# 停止现有进程
echo "[1/7] 停止现有进程..."
pkill -f "python manage.py runserver"
pkill -f "cloudflared tunnel"
sleep 2

# 确保目录结构
echo "[2/7] 创建必要目录..."
mkdir -p static/images/schools/cqtbi

# 爬取学校图片
echo "[3/7] 爬取学校图片..."
python scripts/fetch_cqtbi_images.py

# 在多个端口启动Django服务器
echo "[4/7] 启动Django服务器..."
# 8000端口
python manage.py runserver 0.0.0.0:8000 > django_8000.log 2>&1 &
echo $! > django_8000.pid

# 8080端口 
python manage.py runserver 0.0.0.0:8080 > django_8080.log 2>&1 &
echo $! > django_8080.pid

# 等待服务器启动
echo "[5/7] 等待服务器启动..."
sleep 5

# 检查服务是否正常
echo "[6/7] 检查服务状态..."
SERVICES_OK=0

# 检查8000端口
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ 端口8000服务正常"
    SERVICES_OK=$((SERVICES_OK+1))
else
    echo "❌ 端口8000服务异常"
fi

# 检查8080端口
if curl -s http://localhost:8080/ > /dev/null; then
    echo "✅ 端口8080服务正常"
    SERVICES_OK=$((SERVICES_OK+1))
else
    echo "❌ 端口8080服务异常"
fi

# 启动cloudflared隧道
echo "[7/9] 启动Cloudflare隧道..."
cloudflared tunnel --url http://localhost:8080 > cloudflared.log 2>&1 &
echo $! > cloudflared.pid
sleep 5

# 提取隧道URL
TUNNEL_URL=$(grep -o 'https://.*\.trycloudflare.com' cloudflared.log | tail -1)

# 更新Django设置中的ALLOWED_HOSTS
echo "[8/9] 更新Django设置中的ALLOWED_HOSTS..."
chmod +x scripts/update_allowed_hosts.py
python scripts/update_allowed_hosts.py

# 重启Django服务器以应用新设置
echo "[9/9] 重启Django服务器以应用新设置..."
pkill -f "python manage.py runserver"
sleep 2
python manage.py runserver 0.0.0.0:8000 > django_8000.log 2>&1 &
echo $! > django_8000.pid
python manage.py runserver 0.0.0.0:8080 > django_8080.log 2>&1 &
echo $! > django_8080.pid
sleep 3

# 显示访问信息
echo ""
echo "=========================================="
echo "           访问信息                       "
echo "=========================================="
echo "本地访问: "
echo "  - http://localhost:8000/"
echo "  - http://localhost:8080/"
echo ""
echo "公网访问: "
PUBLIC_IP=$(curl -s ifconfig.me)
echo "  - http://$PUBLIC_IP:8000/ (可能受限制)"
echo "  - http://$PUBLIC_IP:8080/ (可能受限制)"
echo ""
if [ -n "$TUNNEL_URL" ]; then
    echo "Cloudflare隧道访问(推荐): "
    echo "  - $TUNNEL_URL"
else
    echo "Cloudflare隧道URL未找到，请手动查看cloudflared.log"
fi
echo ""
echo "系统状态: $SERVICES_OK/2 项服务正常运行"
echo "=========================================="
echo ""
echo "如果出现'ERR_EMPTY_RESPONSE'错误，请尝试:"
echo "1. 使用Cloudflare隧道URL访问(最可靠)"
echo "2. 重启Django服务器: ./restart_service.sh"
echo "3. 使用SSH隧道: ssh -L 8080:localhost:8080 root@$PUBLIC_IP"
echo "=========================================="