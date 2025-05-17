# Text-to-URL Converter

Text-to-URL Converter 是一个功能强大的工具，能够将文本内容转换为美观的、可通过 URL 访问的网页。特别优化了 Markdown 格式的展示效果，并支持图片插入和自动内容清理。


## 功能特点
1. **文本转 URL 服务**  
   将任意文本内容转换为永久可访问的 URL 链接。

2. **Markdown 支持**  
   自动解析 Markdown 语法，生成美观的 HTML 页面，支持：
   - 标题、列表、代码块
   - 表格、引用、强调
   - 数学公式（需额外配置）

3. **图片处理**  
   - 支持 Base64 图片上传
   - 智能插入图片到文本中
   - 自动调整图片大小以适应页面

4. **自定义标题**  
   可为生成的页面设置自定义标题，增强可读性。

5. **自动内容清理**  
   系统每天自动清理超过 30 天的内容，节省存储空间。

6. **响应式设计**  
   生成的页面在所有设备上都能完美展示，从手机到桌面电脑。


## 使用方法
### 通过 Web 界面
1. 访问应用首页
2. 输入标题（可选）
3. 输入 Markdown 内容
4. 上传 Base64 图片（可选，多行支持多张图片）
5. 点击 "Convert" 生成 URL

### 通过 API
发送 POST 请求到 `/convert` 端点：
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "title": "我的文档标题",
    "content": "这是我的文档内容\n\n包含一些 Markdown 格式",
    "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD..."]
  }' \
  http://localhost:5000/convert
响应示例：{
  "url": "http://localhost:5000/view/8c7c8a2d4f",
  "hash_id": "8c7c8a2d4f",
  "created_at": "2023-05-17T12:34:56.789012"
}

## 图片处理规则
1. 图片会随机插入到文本中的空行位置（由 `\n\n` 分隔）
2. 每个插入点只插入一张图片
3. 多余的图片会添加到文档末尾
4. 图片会自动调整大小以适应页面宽度
5. 所有图片保存在服务器上，并生成唯一文件名


## 部署指南
### 前提条件
- Docker
- Docker Compose (推荐)

### 部署步骤
1. 克隆项目仓库
   ```bash
   git clone https://github.com/your-repo/text-to-url-converter.git
   cd text-to-url-converter
   ```

2. 构建 Docker 镜像
   ```bash
   docker build -t text-to-url .
   ```

3. 运行 Docker 容器
   ```bash
   docker run -d -p 5000:5000 -v $(pwd)/data:/app/data text-to-url
   ```

4. 验证部署
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"content": "Hello, World!"}' \
     http://localhost:5000/convert
   ```


## 配置选项
| 环境变量          | 默认值   | 描述                     |
|-------------------|----------|--------------------------|
| `CLEANUP_INTERVAL` | 86400    | 自动清理间隔时间（秒）   |
| `MAX_AGE_DAYS`     | 30       | 内容保留天数             |
| `PORT`             | 5000     | 服务端口                 |


## 贡献与反馈
如果您发现任何问题或有改进建议，请提交 Issue 或 Pull Request。我们欢迎所有形式的贡献！


## 许可证
本项目采用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。
    