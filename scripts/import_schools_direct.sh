#!/bin/bash

# 直接导入已上传的学校Excel数据
echo "=========================================="
echo "      学校数据导入工具 (直接导入)        "
echo "=========================================="

# 确保目录存在
mkdir -p data

# 检查是否安装了必要的包
echo "[1/2] 检查依赖包..."
pip install pandas openpyxl xlrd -q || { echo "安装依赖包失败"; exit 1; }

# 检查文件是否存在
EXCEL_FILE="$1"
if [ -z "$EXCEL_FILE" ]; then
    echo "错误: 未指定Excel文件路径"
    echo "用法: $0 <Excel文件路径>"
    echo "例如: $0 data/schools.xlsx"
    exit 1
fi

if [ ! -f "$EXCEL_FILE" ]; then
    echo "错误: 文件不存在 - $EXCEL_FILE"
    exit 1
fi

# 导入数据
echo "[2/2] 导入数据到数据库..."
python scripts/import_schools.py "$EXCEL_FILE"

echo ""
echo "=========================================="
echo "学校数据导入完成!"
echo "您可以通过访问以下地址查看更新后的院校库:"
echo "http://localhost:8000/schools/"
echo "或通过Cloudflare隧道访问:"
TUNNEL_URL=$(grep -o 'https://.*\.trycloudflare\.com' cloudflared.log | tail -1)
if [ -n "$TUNNEL_URL" ]; then
    echo "$TUNNEL_URL/schools/"
else
    echo "隧道URL未找到，请检查cloudflared.log"
fi
echo "=========================================="