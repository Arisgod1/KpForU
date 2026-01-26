# KpForU 后端（MVP）

FastAPI + PostgreSQL 实现，遵循提供的 OpenAPI 合约与 Leitner 间隔 `{1:1, 2:2, 3:4, 4:7, 5:14}`。

## 快速开始（Docker）
1) `docker-compose up --build`
2) 打开 http://127.0.0.1:8000/docs （所有路由位于 `/v1`）。

## 本地开发
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/kpforu
export JWT_SECRET_KEY=your-secret
uvicorn app.main:app --reload
```

## 数据库迁移
```bash
alembic upgrade head
```
（使用环境变量 `DATABASE_URL`，默认指向 docker-compose 的 Postgres。）

## Leitner 规则
- 间隔表：`{1:1, 2:2, 3:4, 4:7, 5:14}`（天）
- 激活状态的卡片初始化：box=1，next_review_at = now + interval(1)
- `done`：box +1（最大 5），next_review_at = now + interval(box)
- `snooze`：box 不变，next_review_at += snooze_days（1/2/3）

## 错误格式
统一为：`{ "error": { "code": str, "message": str, "details": object|null } }`

## 文件上传
- `/voice/drafts` 接收 multipart 音频；大小由 `UPLOAD_MAX_MB` 控制（默认 20MB），文件保存在 `storage/voice/` 后由后台 stub 转写处理。

## 关键接口（推荐串联顺序）
1. `POST /v1/devices/watch/register`
2. `POST /v1/binding/pair`
3. `POST /v1/auth/token`
4. 之后带 `Authorization: Bearer <token>`：
   - `POST /v1/timeflows/templates`
   - `POST /v1/focus/sessions`
   - `POST /v1/cards`
   - `POST /v1/reviews/events`（done/snooze）
   - `GET /v1/reviews/due`
   - `GET /v1/watch/review/metrics`
   - `POST /v1/voice/drafts` -> `GET /v1/voice/drafts/{draft_id}`
   - `POST /v1/ai/summaries/daily` / `weekly`

## 测试
- 使用内存 SQLite 覆盖的 pytest：`pytest`

## 环境变量
- `DATABASE_URL`（默认 `postgresql+psycopg2://postgres:postgres@db:5432/kpforu`）
- `JWT_SECRET_KEY`（默认 `dev-secret`）
- `JWT_EXPIRES_SECONDS`（默认 7 天）
- `UPLOAD_MAX_MB`（默认 20）
- `UPLOAD_DIR`（默认 `storage/voice`）
- `X-Client-Timezone` 头影响日期计算。
