import base64
import hashlib
import os
import secrets
import sqlite3
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template_string
from werkzeug.exceptions import BadRequest
from threading import Thread
import socket
import markdown

app = Flask(__name__)
IMAGE_DIR = 'images'
os.makedirs(IMAGE_DIR, exist_ok=True)
DEFAULT_IMAGE = 'default_image.jpg'

# 初始化SQLite数据库
conn = sqlite3.connect('short_urls.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS text_urls
             (short_path TEXT PRIMARY KEY, text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# 获取容器的IP地址
def get_container_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# 配置项
BASE_URL = os.environ.get('BASE_URL', f"http://{get_container_ip()}:5000")
IMAGE_VIEW_PATH = "/view/image/"
TEXT_VIEW_PATH = "/view/text/"
CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', 86400))

# 生成短路径
def generate_short_path(text: str) -> str:
    """生成唯一的短路径，基于文本内容和时间戳"""
    text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:8]
    random_part = os.urandom(4).hex()
    return f"{text_hash}_{random_part}"

# 定期清理任务
def cleanup_task():
    while True:
        try:
            # 清理图片（保留默认图片）
            for filename in os.listdir(IMAGE_DIR):
                if filename != DEFAULT_IMAGE and os.path.isfile(os.path.join(IMAGE_DIR, filename)):
                    file_path = os.path.join(IMAGE_DIR, filename)
                    os.remove(file_path)
                    print(f"Deleted image: {filename}")
            
            # 清理文本数据
            conn = sqlite3.connect('short_urls.db')
            c = conn.cursor()
            c.execute("DELETE FROM text_urls")
            conn.commit()
            conn.close()
            print("All text data has been cleared")
            
            print(f"Cleanup completed at {datetime.now()}")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
        
        # 等待下一个清理周期
        time.sleep(CLEANUP_INTERVAL)

# 启动清理线程
cleanup_thread = Thread(target=cleanup_task)
cleanup_thread.daemon = True
cleanup_thread.start()

# 确保默认图片存在，并且有正确的权限
def ensure_default_image():
    default_path = os.path.join(IMAGE_DIR, DEFAULT_IMAGE)
    if not os.path.exists(default_path):
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (200, 200), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            d.text((70, 90), "No Image", fill=(0, 0, 0))
            img.save(default_path)
            os.chmod(default_path, 0o644)
            print(f"Default image created at {default_path} with permissions 644")
        except ImportError:
            with open(default_path, 'w') as f:
                f.write("Default image placeholder")
            os.chmod(default_path, 0o644)
            print(f"Default image placeholder created at {default_path} with permissions 644")
        except Exception as e:
            print(f"Failed to create default image: {e}")

# 应用启动时确保默认图片存在
ensure_default_image()

@app.route('/image_url', methods=['POST'])
def upload_image():
    """接收base64图片数据，保存图片并返回短链接和路径"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            raise BadRequest('Missing "image" field')
        
        base64_data = data['image']
        filename = secrets.token_hex(16) + '.jpg'
        file_path = os.path.join(IMAGE_DIR, filename)
        
        image_data = base64.b64decode(base64_data)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return jsonify({
            'url': f'{BASE_URL}{IMAGE_VIEW_PATH}{filename}',
            'path': filename
        }), 201
    
    except (BadRequest, base64.binascii.Error) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route(f"{IMAGE_VIEW_PATH}<path:filename>")
def serve_image(filename):
    """根据文件名提供图片服务"""
    file_path = os.path.join(IMAGE_DIR, filename)
    
    if not os.path.isfile(file_path):
        default_path = os.path.join(IMAGE_DIR, DEFAULT_IMAGE)
        if os.path.isfile(default_path):
            try:
                return send_file(default_path, mimetype='image/jpeg')
            except Exception as e:
                print(f"Error serving default image: {e}")
                return jsonify({'error': 'Image not available'}), 500
        else:
            return jsonify({'error': 'Image not found'}), 404
    
    return send_file(file_path, mimetype='image/jpeg')

# 处理文本并生成短链接
@app.route('/text_url', methods=['POST'])
def handle_text_url():
    try:
        # 获取请求中的文本
        if request.is_json:
            data = request.get_json()
            text = data.get('text', '')
        else:
            text = request.form.get('text', '')
        
        if not text:
            return jsonify({"error": "Text content is required"}), 400
        
        # 生成短路径
        short_path = generate_short_path(text)
        
        # 存储映射关系到数据库
        conn = sqlite3.connect('short_urls.db')
        c = conn.cursor()
        c.execute("INSERT INTO text_urls (short_path, text) VALUES (?,?)", (short_path, text))
        conn.commit()
        conn.close()
        
        # 构建完整URL
        full_url = f"{BASE_URL}{TEXT_VIEW_PATH}{short_path}"
        
        return jsonify({
            "url": full_url,
            "path": short_path
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 渲染Markdown页面
@app.route(f"{TEXT_VIEW_PATH}<path:short_path>")
def view_markdown(short_path):
    try:
        # 从数据库中获取原始文本
        conn = sqlite3.connect('short_urls.db')
        c = conn.cursor()
        c.execute("SELECT text FROM text_urls WHERE short_path =?", (short_path,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return jsonify({"error": "Invalid URL"}), 404
        
        text = result[0]
        
        # 将Markdown文本转换为HTML
        html_text = markdown.markdown(text)
        
        # 使用GitHub风格的Markdown渲染
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Markdown Viewer</title>
            <link href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.1.0/github-markdown.min.css" rel="stylesheet">
            <style>
                .markdown-body {{
                    box-sizing: border-box;
                    max-width: 980px;
                    margin: 0 auto;
                    padding: 45px;
                }}
            </style>
        </head>
        <body>
            <article class="markdown-body">{html_text}</article>
        </body>
        </html>
        """
        
        return html_content
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)    