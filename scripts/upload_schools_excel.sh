#!/bin/bash

# 上传学校Excel数据文件并导入到数据库
echo "=========================================="
echo "      学校数据导入工具                    "
echo "=========================================="

# 确保目录存在
mkdir -p data

# 检查是否安装了必要的包
echo "[1/5] 检查依赖包..."
pip install pandas openpyxl xlrd -q || { echo "安装依赖包失败"; exit 1; }

# 提示用户上传文件
echo "[2/5] 准备上传Excel文件..."
echo "请将您的Excel文件上传到服务器。您可以使用以下方法之一："
echo ""
echo "方法1: 使用SCP命令 (在您的本地计算机上运行)"
echo "scp D:\\python\\data\\schools.xlsx root@58.144.141.55:/root/haolaoshi/data/"
echo ""
echo "方法2: 使用SFTP工具 (如FileZilla、WinSCP等)"
echo "主机: 58.144.141.55"
echo "用户名: root"
echo "目标路径: /root/haolaoshi/data/"
echo ""
echo "方法3: 使用Web上传工具"
echo "启动临时Web服务器用于文件上传..."

# 创建简单的上传HTML页面
cat > data/upload.html << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Excel文件上传</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .upload-form { border: 2px dashed #ccc; padding: 20px; text-align: center; }
        .upload-btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; margin-top: 10px; }
        .upload-btn:hover { background: #45a049; }
    </style>
</head>
<body>
    <h1>学校数据Excel文件上传</h1>
    <div class="upload-form">
        <form action="/upload" method="post" enctype="multipart/form-data">
            <h3>选择您的Excel文件</h3>
            <input type="file" name="file" accept=".xlsx,.xls" required>
            <br>
            <button type="submit" class="upload-btn">上传文件</button>
        </form>
    </div>
    <p>上传成功后，请返回终端继续操作。</p>
</body>
</html>
EOF

# 创建Python上传服务器脚本
cat > data/upload_server.py << EOF
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import http.server
import socketserver
import cgi
import time

# 上传目录
UPLOAD_DIR = os.path.dirname(os.path.abspath(__file__))

class FileUploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/upload.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/upload':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            if 'file' in form:
                file_item = form['file']
                if file_item.filename:
                    # 保存文件
                    file_path = os.path.join(UPLOAD_DIR, 'schools.xlsx')
                    with open(file_path, 'wb') as f:
                        f.write(file_item.file.read())
                    
                    # 返回成功页面
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    success_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>上传成功</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                            h1 {{ color: #4CAF50; }}
                            .success {{ background-color: #f0f9f0; border: 1px solid #4CAF50; padding: 20px; border-radius: 5px; }}
                        </style>
                    </head>
                    <body>
                        <h1>文件上传成功!</h1>
                        <div class="success">
                            <p>文件 <strong>{file_item.filename}</strong> 已成功上传到服务器。</p>
                            <p>保存为: <strong>{file_path}</strong></p>
                            <p>现在您可以关闭此页面，并返回终端继续操作。</p>
                        </div>
                    </body>
                    </html>
                    """
                    self.wfile.write(success_html.encode())
                    
                    # 创建标记文件表示上传完成
                    with open(os.path.join(UPLOAD_DIR, 'upload_complete'), 'w') as f:
                        f.write('1')
                    
                    return
            
            # 如果没有文件或出错，返回错误页面
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><head><title>Upload Failed</title></head><body><h1>Upload Failed</h1><p>Please try again.</p></body></html>')

def run_server():
    PORT = 8088
    handler = FileUploadHandler
    handler.cgi_directories = ['/']
    
    # 切换到上传目录
    os.chdir(UPLOAD_DIR)
    
    # 删除之前的完成标记
    if os.path.exists('upload_complete'):
        os.remove('upload_complete')
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"服务器运行在端口 {PORT}...")
        print(f"请访问: http://localhost:{PORT} 或 http://$(curl -s ifconfig.me):{PORT}")
        
        # 运行直到上传完成
        while not os.path.exists('upload_complete'):
            httpd.handle_request()
            time.sleep(0.1)
        
        print("文件上传完成，服务器将关闭")

if __name__ == "__main__":
    run_server()
EOF

# 启动上传服务器
echo "[3/5] 启动临时Web服务器..."
python data/upload_server.py

# 等待文件上传完成
echo "[4/5] 文件已上传，准备导入数据..."
sleep 2

# 导入数据
echo "[5/5] 导入数据到数据库..."
python scripts/import_schools.py data/schools.xlsx

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