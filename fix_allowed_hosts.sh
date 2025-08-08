#!/bin/bash

# 修复DisallowedHost问题的脚本
echo "=========================================="
echo "      修复DisallowedHost问题的脚本        "
echo "=========================================="

# 获取当前的Cloudflare隧道URL
echo "[1/4] 获取Cloudflare隧道URL..."
TUNNEL_URL=$(grep -o 'https://.*\.trycloudflare\.com' cloudflared.log | tail -1)
if [ -z "$TUNNEL_URL" ]; then
    echo "未找到Cloudflare隧道URL，请确保隧道已启动"
    exit 1
fi

DOMAIN=$(echo $TUNNEL_URL | sed 's|https://||')
echo "找到隧道域名: $DOMAIN"

# 修改Django设置文件
echo "[2/4] 修改Django设置文件..."
sed -i "s/ALLOWED_HOSTS = \[/ALLOWED_HOSTS = \[\n    '$DOMAIN',/g" haolaoshi_django/settings.py
echo "已将 $DOMAIN 添加到ALLOWED_HOSTS"

# 重启Django服务器
echo "[3/4] 重启Django服务器..."
pkill -f "python manage.py runserver"
sleep 2
python manage.py runserver 0.0.0.0:8000 > django_8000.log 2>&1 &
echo $! > django_8000.pid
python manage.py runserver 0.0.0.0:8080 > django_8080.log 2>&1 &
echo $! > django_8080.pid
sleep 3

# 检查服务是否正常
echo "[4/4] 检查服务状态..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ 端口8000服务正常"
else
    echo "❌ 端口8000服务异常"
fi

if curl -s http://localhost:8080/ > /dev/null; then
    echo "✅ 端口8080服务正常"
else
    echo "❌ 端口8080服务异常"
fi

echo ""
echo "=========================================="
echo "现在可以通过以下地址访问系统:"
echo "  - $TUNNEL_URL"
echo "如果仍然出现DisallowedHost错误，请尝试以下步骤:"
echo "1. 手动编辑haolaoshi_django/settings.py文件"
echo "2. 在ALLOWED_HOSTS列表中添加'$DOMAIN'"
echo "3. 重启Django服务器"
echo "=========================================="