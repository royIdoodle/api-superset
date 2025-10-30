# OSS 图片资源管理 API

基于 FastAPI + SQLAlchemy + 阿里云 OSS 的图片管理服务，支持图片上传（可选标签/尺寸/格式、TinyPNG 压缩）、查询与统计。

## 功能
- 图片上传：可选参数标签、目标宽高、目标格式（png/jpg/webp）
- TinyPNG 压缩：配置 `TINIFY_API_KEY` 后自动启用
- 图片查询：按 bucket、标签、格式过滤，分页
- 统计：总量、总大小、按格式/按 bucket 分布、近 30 天每日上传量
- 测试页：`/test/upload` 提供上传表单，便于本地验证

## 环境要求
- Python 3.10+
- MySQL 8.0+（或兼容版本）
- 阿里云 OSS 访问凭据

## 快速开始
1. 克隆代码并进入目录
2. 创建并填写环境文件：复制 `ENV.sample` 为 `.env`
3. 安装依赖：
   ```bash
   make setup
   ```
4. 初始化数据库与数据表（会自动创建数据库与表）：
   ```bash
   make db-init
   ```
5. 启动服务：
   ```bash
   make run
   ```
6. 打开接口文档：`http://localhost:8000/docs`，测试页：`http://localhost:8000/test/upload`

## 环境变量
将以下变量写入 `.env`（或以系统环境变量形式注入）：

```dotenv
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=image_oss_manager
MYSQL_USER=root
MYSQL_PASSWORD=password

# Aliyun OSS
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
DEFAULT_OSS_BUCKET=your_bucket

# TinyPNG (可选)
TINIFY_API_KEY=your_tinypng_api_key
```

> 说明：若未配置 `TINIFY_API_KEY`，上传时将跳过压缩/转换，仅直传。

## 运行脚本
- 初始化与安装依赖：`scripts/setup.sh`
- 初始化数据库与表：`scripts/db_init.sh`（`make db-init`）
- 开发启动（含自动重载）：`scripts/run.sh`（`make run`）

## 主要目录
- `app/main.py`：应用入口，注册路由与启动逻辑
- `app/config.py`：配置加载（Pydantic Settings，支持 `.env`）
- `app/database.py`：数据库引擎与会话
- `app/models.py`：SQLAlchemy 模型（`ImageAsset`）
- `app/oss.py`：OSS 客户端封装与上传
- `app/tinify_client.py`：TinyPNG 压缩与可选转换/缩放
- `app/routers/images.py`：上传与查询 API
- `app/routers/stats.py`：统计 API
- `app/routers/test.py`：上传测试页 `/test/upload`

## API 使用示例
- 上传图片
  ```bash
  curl -X POST "http://localhost:8000/images/upload" \
    -F "file=@/path/to/image.png" \
    -F "tags=banner,home" \
    -F "width=1200" -F "height=600" \
    -F "target_format=webp"
  ```

- 查询图片
  ```bash
  curl "http://localhost:8000/images?bucket=your_bucket&tag=banner&fmt=webp&page=1&size=20&order=desc"
  ```

- 查看统计
  ```bash
  curl "http://localhost:8000/stats"
  ```

## 数据表
应用启动时自动创建数据表：
- `image_assets`：存储图片的元数据（文件名、bucket、key、URL、大小、宽高、格式、标签、时间戳）

## 生产部署建议
- 使用独立的 MySQL 实例与只读/只写账号
- OSS Bucket 建议配置为公有读；私有读需改为签名 URL 输出
- 配置进程管理（如 systemd、supervisor、容器编排等）
- 开启应用层日志与访问日志聚合
