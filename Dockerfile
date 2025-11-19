# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY library_app/requirements-test.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements-test.txt

# 复制项目文件
COPY library_app/ .

# 暴露端口（Flask默认5000）
EXPOSE 5000

# 启动命令（生产环境建议使用gunicorn，开发可用flask run）
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]