#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
重庆工商大学图片爬虫，专门用于下载学校官网图片
"""

import os
import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# 基本配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images', 'schools', 'cqtbi')

# 确保图片目录存在
os.makedirs(IMAGES_DIR, exist_ok=True)

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 重庆工商大学官网
CQTBI_URL = "https://www.ctbu.edu.cn/"

def download_image(url, save_path):
    """下载图片并保存到指定路径"""
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logger.info(f"成功下载图片: {url} -> {save_path}")
            return True
    except Exception as e:
        logger.error(f"下载图片失败: {str(e)}")
    return False

def extract_images_from_website(url):
    """从重庆工商大学官网提取图片"""
    try:
        logger.info(f"访问重庆工商大学官网: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 收集所有图片
            images = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if not src:
                    continue
                
                # 处理相对URL
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                
                # 提取图片信息
                alt = img.get('alt', '')
                width = img.get('width', '')
                height = img.get('height', '')
                
                # 只选择有意义的图片
                if src.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                    # 排除图标和小图片
                    if ('icon' not in src.lower() or 'logo' in src.lower()) and \
                       ('thumb' not in src.lower()):
                        images.append({
                            'src': src,
                            'alt': alt,
                            'width': width,
                            'height': height
                        })
            
            # 查找学校标志性大图
            banner_images = []
            for img in images:
                # 标志性特征
                is_banner = False
                if img['alt'] and ('大学' in img['alt'] or '学校' in img['alt'] or '校园' in img['alt']):
                    is_banner = True
                
                # 尺寸大的可能是banner
                try:
                    if img['width'] and img['height'] and \
                       int(img['width']) > 500 and int(img['height']) > 200:
                        is_banner = True
                except:
                    pass
                
                # 文件名特征
                path = urlparse(img['src']).path.lower()
                if 'banner' in path or 'slide' in path or 'header' in path:
                    is_banner = True
                
                if is_banner:
                    banner_images.append(img)
            
            # 如果找到banner图，优先使用
            if banner_images:
                return banner_images
            
            # 否则返回所有图片
            return images
        
    except Exception as e:
        logger.error(f"从网站提取图片失败: {str(e)}")
    
    return []

def update_templates():
    """更新HTML模板中的图片链接"""
    template_files = [
        os.path.join(BASE_DIR, 'templates', 'recommendation', 'school_list.html'),
        os.path.join(BASE_DIR, 'templates', 'recommendation', 'school_detail.html'),
        os.path.join(BASE_DIR, 'templates', 'recommendation', 'recommendation_result.html'),
        os.path.join(BASE_DIR, 'templates', 'recommendation', 'ai_recommendation_result.html')
    ]
    
    for template_file in template_files:
        if not os.path.exists(template_file):
            logger.warning(f"模板文件不存在: {template_file}")
            continue
            
        logger.info(f"更新模板: {template_file}")
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换重庆工商大学的占位图片
            old_img = '<img src="https://via.placeholder.com/400x140?text=重庆工商大学" class="card-img-top" alt="重庆工商大学">'
            new_img = '<img src="/static/images/schools/cqtbi/banner.jpg" class="card-img-top" alt="重庆工商大学">'
            
            if old_img in content:
                content = content.replace(old_img, new_img)
                logger.info(f"成功在 {template_file} 中替换了重庆工商大学的图片")
            else:
                # 尝试更灵活的匹配
                import re
                pattern = r'<img\s+src="https://via\.placeholder\.com/[^"]*\?text=重庆工商大学"\s+class="[^"]*"\s+alt="重庆工商大学">'
                if re.search(pattern, content):
                    content = re.sub(pattern, new_img, content)
                    logger.info(f"成功在 {template_file} 中替换了重庆工商大学的图片")
                else:
                    logger.warning(f"在 {template_file} 中未找到重庆工商大学的占位图片")
            
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            logger.error(f"更新模板失败: {str(e)}")

def main():
    """主函数"""
    logger.info("开始爬取重庆工商大学官网图片")
    
    # 从官网提取图片
    images = extract_images_from_website(CQTBI_URL)
    
    if not images:
        logger.warning("未能从重庆工商大学官网找到有效图片")
        # 尝试使用备用图片
        backup_url = "https://www.baidu.com/s?wd=重庆工商大学"
        logger.info(f"尝试从搜索引擎获取重庆工商大学图片: {backup_url}")
        images = extract_images_from_website(backup_url)
        
        if not images:
            logger.error("无法获取重庆工商大学图片")
            return
    
    # 下载图片
    success = False
    for i, img in enumerate(images):
        image_ext = os.path.splitext(urlparse(img['src']).path)[1] or '.jpg'
        if not image_ext.startswith('.'):
            image_ext = f".{image_ext}"
            
        # 主图片保存为banner.jpg
        if i == 0:
            save_path = os.path.join(IMAGES_DIR, f"banner{image_ext}")
            if download_image(img['src'], save_path):
                # 统一转换为jpg格式
                if image_ext != '.jpg':
                    try:
                        from PIL import Image
                        img_obj = Image.open(save_path)
                        jpg_path = os.path.join(IMAGES_DIR, "banner.jpg")
                        img_obj.convert('RGB').save(jpg_path, 'JPEG')
                        logger.info(f"已将图片转换为JPG格式: {jpg_path}")
                    except Exception as e:
                        logger.warning(f"图片格式转换失败: {str(e)}")
                        # 如果转换失败，直接复制
                        shutil.copy(save_path, os.path.join(IMAGES_DIR, "banner.jpg"))
                success = True
                
        # 其他图片保存为images/x.jpg
        elif i < 5:  # 最多保存5张
            save_path = os.path.join(IMAGES_DIR, f"image_{i}{image_ext}")
            download_image(img['src'], save_path)
    
    if success:
        # 更新HTML模板
        update_templates()
        logger.info("重庆工商大学图片爬取和更新完成")
    else:
        logger.error("未能成功下载重庆工商大学图片")

if __name__ == "__main__":
    main()