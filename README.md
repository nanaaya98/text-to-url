# Share_Url 项目文档

## 简介
Share_Url 是一个基于 Flask 的 Web 应用程序，用于生成图片和文本的短链接。用户可以上传 Base64 编码的图片或提供文本内容，系统会为其生成唯一的短链接，方便分享。同时，该应用具备定期清理功能，可自动删除过期的图片和文本数据。

## 功能特性
1. **图片短链接生成**：接收 Base64 编码的图片数据，保存图片并返回短链接。
2. **文本短链接生成**：接收文本内容，生成唯一的短路径并存储到数据库，返回对应的短链接。
3. **Markdown 渲染**：支持将文本内容以 Markdown 格式渲染为 HTML 页面。
4. **定期清理**：按照指定的时间间隔自动清理过期的图片和文本数据。

## 环境要求
- Python 3.x
- Docker（可选）

## 安装依赖
### 手动安装
在项目根目录下，执行以下命令安装所需的 Python 包：pip install -r requirements.txt### 使用 Docker 安装
如果你使用 Docker 部署项目，可以使用以下命令构建和启动容器：docker-compose up -d
## 配置项
### 环境变量
- `BASE_URL`：应用的基础 URL，默认为 `http://localhost:5000`。可以根据实际情况修改为域名或 IP 地址。
- `CLEANUP_INTERVAL`：清理间隔时间（秒），默认为 86400 秒（即 24 小时）。

### 修改配置
可以在 `docker-compose.yml` 文件中修改环境变量的值：environment:
  - BASE_URL=http://yourdomain.com
  - CLEANUP_INTERVAL=43200  # 清理间隔为 12 小时
## 使用方法
### 上传图片并获取短链接
发送 POST 请求到 `/image_url` 接口，请求体为 JSON 格式，包含 `image` 字段，其值为 Base64 编码的图片数据。curl -X POST -H "Content-Type: application/json" -d '{"image": "your_base64_image_data"}' http://localhost:5000/image_url响应示例：{
    "url": "http://localhost:5000/view/image/your_image_filename.jpg",
    "path": "your_image_filename.jpg"
}
### 处理文本并获取短链接
发送 POST 请求到 `/text_url` 接口，请求体可以是 JSON 格式或表单数据，包含 `text` 字段，其值为文本内容。curl -X POST -H "Content-Type: application/json" -d '{"text": "your_text_content"}' http://localhost:5000/text_url响应示例：{
    "url": "http://localhost:5000/view/text/your_short_path",
    "path": "your_short_path"
}
### 查看 Markdown 页面
访问生成的文本短链接，即可查看渲染后的 Markdown 页面。http://localhost:5000/view/text/your_short_path
## 代码结构
- `app.py`：主应用程序文件，包含 Flask 路由和业务逻辑。
- `requirements.txt`：Python 依赖包列表。
- `docker-compose.yml`：Docker 配置文件，用于部署应用。
- `short_urls.db`：SQLite 数据库文件，用于存储文本短路径和内容的映射关系。
- `images/`：图片存储目录。

## 版权信息
本项目采用 MIT 许可证，详情请参阅 `LICENSE` 文件。

## 贡献
如果你想为该项目做出贡献，请提交 Pull Request 或提出 Issue。

## 作者
Nanaaya

## 版本信息
当前版本：1.0.0

以上文档提供了 Share_Url 项目的详细介绍、安装步骤、使用方法和代码结构等信息，帮助用户快速上手和使用该项目。
    