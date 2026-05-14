# 企业职工宿舍入住管理系统

Python 3.11 + FastAPI（SQLAlchemy + **asyncpg**）+ Vue 3（Vite + Element Plus）+ PostgreSQL 16，使用 Docker Compose 一键启动。详细需求见根目录 `prompt.txt`。

## 功能概览

- **宿舍台账**：楼栋（楼号/性别/层数）、房间（房型单/四/六人间、正常/维修）、按房间类型自动生成床位编号  
- **入住**：员工提交申请 → 管理员审批 → 选择空闲床位下达入住（押金、钥匙）→ 床位视图展示占用  
- **调换**：申请 → 审批 → 执行换床并写入调换历史  
- **退住**：申请 → 审批 → 宿管查房（损坏/描述）、退押金、钥匙归还  
- **费用**：房型月租配置、按月批量生成账单、实收入账、欠缴提醒次数、年度按月汇总  
- **报修**：住户按入住记录报修（绑定房间）、派单、完成与 1～5 星评价  

## 数据与预置种子

表结构在 `db/init.sql` 中建表；要求中的核心表 **`dormitories`、`rooms`、`beds`、`checkin_records`、`fee_records`** 均存在。另含申请/调换/退住/报修等支撑表。

初始化脚本会插入 **10 栋宿舍、200 间房、全部床位**，以及约 **72** 条预置在住记录与样例账单、报修工单。

## 快速启动（Docker）

在包含 **`docker-compose.yml`** 的目录执行（在 **`*-model`** 工作区中即 **`repo/`**）：

```bash
docker compose up -d --build
```

浏览器访问：**http://localhost:8080**（前端 nginx，API 同源 `/api/` 反代）。

排错时可查看 API 健康：

```bash
docker compose exec api curl -s http://localhost:8000/health
```

## 常用 Compose 命令

```bash
docker compose logs -f api
docker compose down -v
```

`docker compose down -v` 会移除 Compose 定义的卷（Postgres 开发数据会清空）。

## 本地开发（可选）

- **后端**：建议使用 Python **3.11**（与 Docker 镜像一致）。依赖含 **asyncpg**；若当前环境无法安装预编译包，请仅用 Docker 构建/运行后端。  
- **前端**：`cd frontend && npm install && npm run dev`（必要时设置 `VITE_API_BASE`；Compose 构建默认 `/api`。）

## 自动化测试

在 API 镜像（Python 3.11）中运行（单测会将 `DATABASE_URL` 指向 SQLite 内存，不依赖本机 PostgreSQL）：

```bash
docker compose build api
docker compose run --rm --no-deps api pytest tests/ -v
```

## 项目结构

```
repo/  （模型中：021_dormitory-model/repo/）
  docker-compose.yml
  db/init.sql
  backend/
  frontend/
  prompt.txt
```
