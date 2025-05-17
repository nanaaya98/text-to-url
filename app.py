from flask import Flask, render_template_string, request, jsonify
import markdown
from datetime import datetime, timedelta
import hashlib
import os
import threading
import time
import base64
import random
from PIL import Image
from io import BytesIO

app = Flask(__name__)
DATA_DIR = 'data'
IMAGES_DIR = os.path.join(DATA_DIR, 'images')
CLEANUP_INTERVAL = 86400  # 24小时
MAX_AGE_DAYS = 30  # 30天

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

def cleanup_task():
    """定期清理任务，每24小时执行一次，删除超过30天的文件"""
    while True:
        try:
            print("Starting cleanup task...")
            now = datetime.now()
            for filename in os.listdir(DATA_DIR):
                file_path = os.path.join(DATA_DIR, filename)
                if os.path.isfile(file_path):
                    # 获取文件创建时间
                    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    # 如果文件年龄超过30天，则删除
                    if (now - creation_time).days > MAX_AGE_DAYS:
                        os.remove(file_path)
                        print(f"Deleted old file: {filename}")
            print("Cleanup task completed.")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
        # 等待24小时后再次执行
        time.sleep(CLEANUP_INTERVAL)

def process_images(images_data):
    """处理图片数据并保存到本地"""
    image_paths = []
    for i, img_data in enumerate(images_data):
        try:
            # 移除可能存在的前缀
            if img_data.startswith('data:image/'):
                img_data = img_data.split(',', 1)[1]
            
            # 解码base64数据
            img_bytes = base64.b64decode(img_data)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            hash_str = hashlib.sha256((img_data + timestamp).encode()).hexdigest()[:10]
            file_ext = get_image_extension(img_bytes)
            filename = f'{hash_str}.{file_ext}'
            file_path = os.path.join(IMAGES_DIR, filename)
            
            # 保存图片
            with open(file_path, 'wb') as f:
                f.write(img_bytes)
            
            image_paths.append(filename)
        except Exception as e:
            print(f"Error processing image {i}: {str(e)}")
            continue
    return image_paths

def get_image_extension(img_bytes):
    """根据图片内容确定文件扩展名"""
    try:
        img = Image.open(BytesIO(img_bytes))
        return img.format.lower()
    except:
        return 'jpg'

def insert_images_into_text(content, image_paths):
    """将图片随机插入到文本中的空行位置"""
    if not image_paths:
        return content
    
    # 按空行分割文本
    blocks = content.split('\n\n')
    
    # 计算可插入图片的位置（至少有一个其他块）
    if len(blocks) <= 1:
        # 如果没有空行，直接在末尾添加所有图片
        image_md = '\n\n'.join([f'![Image](images/{img_path})' for img_path in image_paths])
        return content + '\n\n' + image_md
    
    # 随机选择位置插入图片
    positions = sorted(random.sample(range(len(blocks)), min(len(blocks)-1, len(image_paths))))
    images_used = 0
    
    new_blocks = []
    for i, block in enumerate(blocks):
        new_blocks.append(block)
        if i in positions and images_used < len(image_paths):
            new_blocks.append(f'![Image](images/{image_paths[images_used]})')
            images_used += 1
    
    # 添加剩余的图片到末尾
    if images_used < len(image_paths):
        for img_path in image_paths[images_used:]:
            new_blocks.append(f'![Image](images/{img_path})')
    
    return '\n\n'.join(new_blocks)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text to URL</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            textarea { width: 100%; height: 200px; margin-bottom: 10px; font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace; }
            .markdown-content { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
            .markdown-content h1, .markdown-content h2, .markdown-content h3 { border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
            .markdown-content pre { background-color: #f6f8fa; border-radius: 3px; font-size: 85%; line-height: 1.45; overflow: auto; padding: 16px; }
            .markdown-content code { background-color: rgba(27,31,35,0.05); border-radius: 3px; font-size: 85%; margin: 0; padding: 0.2em 0.4em; }
            .markdown-content blockquote { border-left: 0.25em solid #dfe2e5; color: #6a737d; padding: 0 1em; }
            .markdown-content img { max-width: 100%; height: auto; }
        </style>
    </head>
    <body>
        <h1>Text to URL Converter</h1>
        <form method="POST" action="/convert">
            <label for="title">Title (optional):</label>
            <input type="text" id="title" name="title" placeholder="Enter title here..."><br><br>
            
            <label for="text">Content:</label><br>
            <textarea name="text" placeholder="Enter your text or markdown here..."></textarea><br>
            
            <label for="images">Images (base64, multiple allowed, comma-separated):</label><br>
            <textarea id="images" name="images" placeholder="Paste base64 image data here..."></textarea><br>
            
            <button type="submit">Convert</button>
        </form>
    </body>
    </html>
    ''')

@app.route('/convert', methods=['POST'])
def convert():
    """通过HTTP POST请求接收文本并返回生成的URL"""
    # 支持从JSON或表单数据中获取文本
    if request.is_json:
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')
        images = data.get('images', [])
    else:
        title = request.form.get('title', '')
        content = request.form.get('text', '')
        images = request.form.get('images', '').split('\n')
        images = [img.strip() for img in images if img.strip()]
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    # 处理图片
    image_paths = process_images(images)
    
    # 插入图片到文本中
    final_content = insert_images_into_text(content, image_paths)
    
    # 如果有标题，添加标题
    if title:
        final_content = f'# {title}\n\n{final_content}'
    
    # 添加尾注
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_content += f'\n\n---\n\n喵子柒 &emsp;&emsp;&emsp;&emsp;{timestamp}'
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    hash_str = hashlib.sha256((content + timestamp).encode()).hexdigest()[:10]
    filename = f'{DATA_DIR}/{hash_str}.txt'
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_content)
    except Exception as e:
        return jsonify({'error': f'Failed to save content: {str(e)}'}), 500
    
    return jsonify({
        'url': f'{request.host_url}view/{hash_str}',
        'hash_id': hash_str,
        'created_at': datetime.now().isoformat()
    })

@app.route('/view/<hash_id>')
def view(hash_id):
    """查看生成的内容页面"""
    filename = f'{DATA_DIR}/{hash_id}.txt'
    
    if not os.path.exists(filename):
        return jsonify({'error': 'Content not found'}), 404
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return jsonify({'error': f'Failed to read content: {str(e)}'}), 500
    
    try:
        # 尝试将内容解析为Markdown
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>View Content</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 45px; }
                .markdown-content { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
                .markdown-content h1, .markdown-content h2, .markdown-content h3 { border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
                .markdown-content pre { background-color: #f6f8fa; border-radius: 3px; font-size: 85%; line-height: 1.45; overflow: auto; padding: 16px; }
                .markdown-content code { background-color: rgba(27,31,35,0.05); border-radius: 3px; font-size: 85%; margin: 0; padding: 0.2em 0.4em; }
                .markdown-content blockquote { border-left: 0.25em solid #dfe2e5; color: #6a737d; padding: 0 1em; }
                .markdown-content img { max-width: 100%; height: auto; }
                .markdown-content hr { background-color: #e1e4e8; border: 0; height: 0.25em; margin: 24px 0; padding: 0; }
                .markdown-content table { border-collapse: collapse; display: block; overflow: auto; width: 100%; }
                .markdown-content table th { border: 1px solid #dfe2e5; font-weight: 600; padding: 6px 13px; }
                .markdown-content table td { border: 1px solid #dfe2e5; padding: 6px 13px; }
                .markdown-content table tr { background-color: #fff; border-top: 1px solid #c6cbd1; }
                .markdown-content table tr:nth-child(2n) { background-color: #f6f8fa; }
            </style>
        </head>
        <body>
            <div class="markdown-content">
                {{ content|safe }}
            </div>
        </body>
        </html>
        ''', content=html_content)
    except:
        # 如果解析失败，以纯文本形式显示
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>View Content</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 45px; }
                pre { white-space: pre-wrap; word-wrap: break-word; }
            </style>
        </head>
        <body>
            <pre>{{ content }}</pre>
        </body>
        </html>
        ''', content=content)

@app.route('/api/status', methods=['GET'])
def status():
    """返回服务状态信息"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'uptime': time.time() - app.start_time,
        'total_files': len(os.listdir(DATA_DIR))
    })

if __name__ == '__main__':
    # 记录应用启动时间
    app.start_time = time.time()
    
    # 启动清理线程
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000)    