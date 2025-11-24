# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装构建依赖以便能构建/安装 cryptography（包含 cargo，用于新版 cryptography 需要 Rust）
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libssl-dev libffi-dev python3-dev cargo && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 升级 pip 并安装 cryptography（确保 PyMySQL 所需的加密支持可用），然后安装其他依赖
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir cryptography && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口（Flask默认5000）
EXPOSE 5000

# 启动命令（生产环境建议使用gunicorn，开发可用flask run）
CMD ["gunicorn", "--bind", "0.0.0.0:5000","app:app"]