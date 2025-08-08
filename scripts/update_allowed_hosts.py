#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
更新Django设置中的ALLOWED_HOSTS，自动添加Cloudflare隧道域名
"""

import os
import re
import sys

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, 'haolaoshi_django', 'settings.py')
CLOUDFLARED_LOG = os.path.join(BASE_DIR, 'cloudflared.log')

def get_tunnel_url():
    """从cloudflared日志中提取隧道URL"""
    if not os.path.exists(CLOUDFLARED_LOG):
        print(f"错误: 找不到Cloudflared日志文件: {CLOUDFLARED_LOG}")
        return None
    
    try:
        with open(CLOUDFLARED_LOG, 'r') as f:
            content = f.read()
            
        # 使用正则表达式匹配隧道URL
        match = re.search(r'https://([a-zA-Z0-9-]+\.trycloudflare\.com)', content)
        if match:
            return match.group(1)
        else:
            print("错误: 在日志文件中未找到隧道URL")
            return None
    except Exception as e:
        print(f"读取日志文件时出错: {str(e)}")
        return None

def update_settings(tunnel_domain):
    """更新Django设置文件中的ALLOWED_HOSTS"""
    if not os.path.exists(SETTINGS_FILE):
        print(f"错误: 找不到Django设置文件: {SETTINGS_FILE}")
        return False
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            content = f.read()
        
        # 检查域名是否已经在ALLOWED_HOSTS中
        allowed_hosts_pattern = r'ALLOWED_HOSTS\s*=\s*\[(.*?)\]'
        match = re.search(allowed_hosts_pattern, content, re.DOTALL)
        
        if not match:
            print("错误: 在设置文件中未找到ALLOWED_HOSTS")
            return False
        
        allowed_hosts = match.group(1)
        
        # 检查域名是否已经存在
        if f"'{tunnel_domain}'" in allowed_hosts or f'"{tunnel_domain}"' in allowed_hosts:
            print(f"域名 {tunnel_domain} 已经在ALLOWED_HOSTS中")
            return True
        
        # 添加新域名
        new_allowed_hosts = f"""ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '{tunnel_domain}',
    '.trycloudflare.com',  # 允许所有cloudflare隧道域名
    '58.144.141.55',  # 服务器IP
]"""
        
        # 替换ALLOWED_HOSTS
        new_content = re.sub(allowed_hosts_pattern, new_allowed_hosts, content, flags=re.DOTALL)
        
        with open(SETTINGS_FILE, 'w') as f:
            f.write(new_content)
        
        print(f"成功将 {tunnel_domain} 添加到ALLOWED_HOSTS")
        return True
    
    except Exception as e:
        print(f"更新设置文件时出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("更新Django设置中的ALLOWED_HOSTS...")
    
    # 获取隧道域名
    tunnel_domain = get_tunnel_url()
    if not tunnel_domain:
        print("未找到有效的隧道域名，将只允许本地访问")
        tunnel_domain = "example.trycloudflare.com"
    
    # 更新设置
    success = update_settings(tunnel_domain)
    
    if success:
        print("设置更新成功")
        print(f"现在可以通过以下地址访问系统:")
        print(f"  - http://{tunnel_domain}/")
        print(f"  - https://{tunnel_domain}/")
    else:
        print("设置更新失败")
        sys.exit(1)

if __name__ == "__main__":
    main()