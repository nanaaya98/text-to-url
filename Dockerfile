# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV BASE_URL=http://localhost:5000
ENV CLEANUP_INTERVAL=86400

# 创建存储图片的目录
RUN mkdir -p images

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["python", "app.py"]    