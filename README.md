# Library App 项目文档

## 本地开发与测试 (WSL2)

本项目包含一个专门用于本地开发的 Docker Compose 配置文件 `docker-compose-local.yml`。

### 前置条件
1. 安装 Docker Desktop 并启用 WSL2 集成。
2. 确保终端位于项目根目录 `library_app/` 下。

### 启动本地环境

使用以下命令构建并启动服务（包含 Web 应用和 MySQL 数据库）：

```bash
docker-compose -f docker-compose-local.yml up --build
```

- **Web 服务**: 运行在 `http://localhost:5000`
- **数据库**: 端口映射为 `33060` (避免与本地 MySQL 冲突)
- **热重载**: 本地代码目录已挂载到容器中，修改代码后无需重建镜像。

### 停止环境

测试完成后，按 `Ctrl+C` 停止运行，或在另一个终端执行：

```bash
docker-compose -f docker-compose-local.yml down
```

如果要同时删除数据卷（清空数据库数据）：

```bash
docker-compose -f docker-compose-local.yml down -v
```

## 服务器部署

在生产服务器上，推荐使用 `docker-compose` 进行统一管理。

1. 确保项目根目录下有 `docker-compose.yml` 文件（生产环境配置）。
2. 启动服务（后台运行）：
   ```bash
   docker-compose up -d --build
   ```
3. 查看日志：
   ```bash
   docker-compose logs -f
   ```
4. 停止服务：
   ```bash
   docker-compose down
   ```
