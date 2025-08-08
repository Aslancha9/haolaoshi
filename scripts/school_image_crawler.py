#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学校图片爬虫脚本，自动下载学校官网图片替换占位图
"""

import os
import re
import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin, urlparse
import sqlite3
import logging
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("school_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SchoolCrawler")

# 基本配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images', 'schools')
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')

# 确保图片目录存在
os.makedirs(IMAGES_DIR, exist_ok=True)

# 常见的搜索引擎和搜索模式
SEARCH_ENGINES = {
    "百度": "https://www.baidu.com/s?wd={school_name}+官网",
    "搜狗": "https://www.sogou.com/web?query={school_name}+官网",
}

# 请求头，模拟浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 可能的标志性图片关键字
LOGO_KEYWORDS = ['logo', 'title', 'header', 'banner', 'school', 'university']
BANNER_KEYWORDS = ['banner', 'slide', 'carousel', 'header', 'top']

def get_schools_from_db():
    """从数据库获取学校列表"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, website FROM recommendation_school")
        schools = cursor.fetchall()
        conn.close()
        return schools
    except Exception as e:
        logger.error(f"从数据库获取学校信息失败: {str(e)}")
        return []

def get_school_website(school_name):
    """通过搜索引擎获取学校官网"""
    for engine_name, search_url in SEARCH_ENGINES.items():
        try:
            url = search_url.format(school_name=school_name)
            logger.info(f"通过{engine_name}搜索 {school_name} 官网")
            
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取搜索结果中的第一个链接
                if engine_name == "百度":
                    result_links = soup.select('.result h3 a')
                elif engine_name == "搜狗":
                    result_links = soup.select('.vrwrap h3 a')
                
                if result_links:
                    href = result_links[0].get('href')
                    
                    # 对于百度搜索，需要再次请求真实链接
                    if engine_name == "百度":
                        try:
                            real_url_response = requests.get(href, headers=HEADERS, timeout=5, allow_redirects=True)
                            return real_url_response.url
                        except:
                            continue
                    else:
                        return href
            
            # 避免请求过于频繁
            time.sleep(2 + random.random())
            
        except Exception as e:
            logger.error(f"搜索{school_name}官网时出错: {str(e)}")
            continue
    
    return None

def update_school_website_in_db(school_id, website):
    """更新数据库中的学校官网"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE recommendation_school SET website = ? WHERE id = ?", (website, school_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"更新学校官网失败: {str(e)}")
        return False

def download_image(url, save_path):
    """下载图片并保存到指定路径"""
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        logger.error(f"下载图片失败: {str(e)}")
    return False

def extract_images_from_website(url, school_name):
    """从学校官网提取图片"""
    try:
        logger.info(f"访问 {school_name} 官网: {url}")
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
                
                # 提取有价值的属性
                alt = img.get('alt', '').lower()
                class_name = ' '.join(img.get('class', [])).lower()
                img_id = img.get('id', '').lower()
                
                # 计算图片的可能重要性分数
                importance = 0
                
                # 检查文件名、alt、class和id是否包含关键字
                path = urlparse(src).path.lower()
                
                # Logo相关评分
                for keyword in LOGO_KEYWORDS:
                    if keyword in path or keyword in alt or keyword in class_name or keyword in img_id:
                        importance += 5
                
                # Banner相关评分
                for keyword in BANNER_KEYWORDS:
                    if keyword in path or keyword in alt or keyword in class_name or keyword in img_id:
                        importance += 3
                
                # 如果URL或alt中包含学校名称，增加重要性
                if school_name.lower() in path.lower() or school_name.lower() in alt.lower():
                    importance += 10
                
                # 排除非图片文件和图标
                if not src.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                    continue
                
                if 'icon' in path.lower() and 'logo' not in path.lower():
                    continue
                
                images.append({
                    'src': src,
                    'importance': importance,
                    'alt': alt,
                    'class': class_name,
                    'id': img_id
                })
            
            # 按重要性排序
            images.sort(key=lambda x: x['importance'], reverse=True)
            return images[:10]  # 返回最重要的10张图片
        
    except Exception as e:
        logger.error(f"从网站提取图片失败: {str(e)}")
    
    return []

def process_school(school):
    """处理单个学校"""
    school_id, school_name, website = school
    
    # 如果数据库中没有官网链接，尝试获取
    if not website:
        website = get_school_website(school_name)
        if website:
            update_school_website_in_db(school_id, website)
        else:
            logger.warning(f"无法找到 {school_name} 的官网")
            return False
    
    # 从官网提取图片
    images = extract_images_from_website(website, school_name)
    
    if not images:
        logger.warning(f"未能从 {school_name} 官网找到有效图片")
        return False
    
    # 为学校创建目录
    school_dir = os.path.join(IMAGES_DIR, str(school_id))
    os.makedirs(school_dir, exist_ok=True)
    
    # 下载最重要的图片
    top_image = images[0]
    image_ext = os.path.splitext(urlparse(top_image['src']).path)[1] or '.jpg'
    banner_path = os.path.join(school_dir, f"banner{image_ext}")
    
    if download_image(top_image['src'], banner_path):
        logger.info(f"成功下载 {school_name} 的主图片")
        
        # 如果有多个图片，再保存一个作为logo
        if len(images) > 1:
            logo_candidate = next((img for img in images if 'logo' in img['alt'].lower() or 
                                  'logo' in img['class'].lower() or 
                                  'logo' in img['id'].lower()), images[1])
            
            logo_ext = os.path.splitext(urlparse(logo_candidate['src']).path)[1] or '.png'
            logo_path = os.path.join(school_dir, f"logo{logo_ext}")
            
            if download_image(logo_candidate['src'], logo_path):
                logger.info(f"成功下载 {school_name} 的Logo")
        
        return {
            'school_id': school_id,
            'school_name': school_name,
            'banner_path': os.path.relpath(banner_path, STATIC_DIR),
            'success': True
        }
    
    logger.warning(f"下载 {school_name} 图片失败")
    return False

def update_templates(results):
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
            
            for result in results:
                if not result or not isinstance(result, dict) or not result.get('success'):
                    continue
                    
                school_name = result['school_name']
                banner_path = result['banner_path']
                
                # 替换占位图片
                placeholder_pattern = r'<img\s+src="https://via\.placeholder\.com/[^"]*\?text={0}"\s+class="[^"]*"\s+alt="{0}">'.format(re.escape(school_name))
                replacement = f'<img src="/static/{banner_path}" class="card-img-top" alt="{school_name}">'
                
                content = re.sub(placeholder_pattern, replacement, content)
            
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"成功更新模板: {template_file}")
            
        except Exception as e:
            logger.error(f"更新模板失败: {str(e)}")

def main():
    """主函数"""
    logger.info("开始爬取学校图片")
    
    # 从数据库获取学校
    schools = get_schools_from_db()
    if not schools:
        logger.error("未找到学校信息，请检查数据库")
        return
    
    logger.info(f"共找到 {len(schools)} 所学校")
    
    # 使用线程池并行处理
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for result in executor.map(process_school, schools):
            if result:
                results.append(result)
    
    logger.info(f"成功下载 {len(results)} 所学校的图片")
    
    # 更新HTML模板
    update_templates(results)
    
    logger.info("图片爬取和更新完成")

if __name__ == "__main__":
    main()