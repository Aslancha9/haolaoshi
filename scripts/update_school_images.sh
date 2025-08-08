#!/bin/bash

# 图片爬取和更新脚本

echo "=== 开始更新学校图片 ==="

# 切换到项目根目录
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# 创建图片目录
mkdir -p static/images/schools/cqtbi

echo "=== 爬取重庆工商大学图片 ==="
python scripts/fetch_cqtbi_images.py

echo "=== 检查Django服务器状态 ==="
if pgrep -f "python manage.py runserver" > /dev/null; then
    echo "Django服务器正在运行，无需重启"
else
    echo "Django服务器未运行，启动服务..."
    nohup python manage.py runserver 0.0.0.0:8000 > django_server.log 2>&1 &
    echo "Django服务器已在后台启动，PID: $!"
fi

echo "=== 图片更新完成 ==="
echo "现在可以通过浏览器访问: http://localhost:8000/"
echo "或公网地址: http://$(curl -s ifconfig.me):8000/"