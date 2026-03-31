# KpForU 后端

基于 FastAPI + SQLAlchemy 的 API 服务，负责设备绑定鉴权、时间流/专注/复习数据、语音建卡与 AI 总结导出。

## 技术栈
- FastAPI / Pydantic
- SQLAlchemy / Alembic
- PostgreSQL（生产）/ SQLite（本地自测可用）
- Qwen OpenAI-Compatible 接口（语音与总结）

## 本地启动（推荐 conda）
1. 激活环境：`conda activate kpforu-server`
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量（至少 `DATABASE_URL`、`JWT_SECRET_KEY`、`DASHSCOPE_API_KEY`）
4. 在 `server` 目录启动：`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
5. 打开文档：`http://127.0.0.1:8000/docs`

## 一键启动脚本（Windows）
- 脚本路径：`server/scripts/start_backend.ps1`、`server/scripts/start_backend.bat`
- 用法（推荐）：
	- `powershell -ExecutionPolicy Bypass -File .\server\scripts\start_backend.ps1 -BindHost 127.0.0.1 -Port 8000`
	- `server\scripts\start_backend.bat -BindHost 127.0.0.1 -Port 8000`
	- 若未配置数据库，可加 `-UseSqlite` 自动切换到 `sqlite+pysqlite:///./runtime.db`
- 特性：
	- 自动提示当前 conda 环境是否为 `kpforu-server`
	- 自动优先使用 `kpforu-server` 的 Python 解释器
	- 在缺失 `DATABASE_URL` 时可回退 SQLite

## Docker 启动
- 在 `server` 目录执行：`docker-compose up --build`

## 关键接口
### 绑定与鉴权
- `POST /v1/devices/watch/register`
- `POST /v1/binding/pair`
- `POST /v1/auth/token`

### 时间流与专注
- `GET/POST/PUT/DELETE /v1/timeflows/templates`
- `GET/POST/DELETE /v1/focus/sessions`

### 复习与卡片
- `GET /v1/reviews/due`
- `POST /v1/reviews/events`
- `GET/POST/PUT/DELETE /v1/cards`
- `GET /v1/watch/review/metrics`
- `GET /v1/watch/wallpaper`
- `PUT /v1/watch/wallpaper`

### AI 与语音
- `POST /v1/voice/drafts`
- `GET /v1/voice/drafts/{draft_id}`（含 `transcript_text`）
- `POST /v1/ai/summaries/daily`
- `POST /v1/ai/summaries/weekly`
- `POST /v1/ai/exports/learning-pdf`

## 大模型调用与日志排查

后端已增加统一日志埋点，用于区分“真实调用成功”与“fallback 回退”。

- 文本/音频调用：`LLM_CALL_START` / `LLM_CALL_OK` / `LLM_CALL_ERROR`
- AI 总结：`LLM_SUMMARY_START` / `LLM_SUMMARY_OK` / `LLM_SUMMARY_FALLBACK`
- 导出总结：`LLM_EXPORT_SUMMARY_START` / `LLM_EXPORT_SUMMARY_OK` / `LLM_EXPORT_SUMMARY_FALLBACK`
- 语音草稿：`VOICE_DRAFT_PROCESS_START` / `VOICE_DRAFT_LLM_OK` / `VOICE_DRAFT_LLM_FALLBACK`

说明：
- AI 总结、导出、语音在模型失败时都存在 fallback 逻辑，因此“接口 200”不等于“模型调用成功”。
- 请结合上述日志关键词判断真实调用状态。

## DashScope 兼容调用说明

- 采用 OpenAI-compatible 接口，默认北京域名：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- `DASHSCOPE_API_KEY` 必须通过环境变量注入（不应硬编码到仓库）
- Qwen-Omni 调用使用流式输出（`stream=True`）
- 本地音频上传时使用 data URL（`data:audio/...;base64,...`）以兼容参数校验

## 大模型等待边界（服务端）

- 配置项位置：`app/core/config.py`
- `qwen_timeout_seconds`：单次模型请求超时（默认 `60` 秒）
- `qwen_max_retries`：瞬时失败重试次数（默认 `1`）

说明：
- 当模型端响应慢时，服务端会在超时后触发错误路径，并由上层总结/导出/语音流程决定 fallback。
- 建议与客户端超时策略配合调优，避免“客户端先超时”或“服务端等待过久”。

## 学习导出（PDF）

- 中文字体已适配，避免中文乱码
- 导出内容包含“学习总计”（专注总时长、平均时长、复习完成率等）

## 语音上传约束
- 接口：`POST /v1/voice/drafts`
- 格式：`multipart/form-data`
- 文件字段名：`file`
- 存储目录：`UPLOAD_DIR`（默认 `storage/voice`）

## Leitner 规则
- 间隔表：`{1:1, 2:2, 3:4, 4:7, 5:14}`（单位：天）
- `done`：盒子等级提升（上限 5）并刷新 `next_review_at`
- `snooze`：盒子等级不变，按 1/2/3 天顺延

## 测试
- 单测：`pytest`
- 已验证链路：语音草稿创建/查询、学习总结 PDF 导出。

## CI 质量门禁
- 工作流：`.github/workflows/quality-gate.yml`
- 包含：
	- 后端：`pytest tests/test_flow.py -q`
	- 手机端：`flutter analyze`

## 主要环境变量
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_EXPIRES_SECONDS`
- `DASHSCOPE_API_KEY`
- `QWEN_TIMEOUT_SECONDS`
- `QWEN_MAX_RETRIES`
- `UPLOAD_MAX_MB`
- `UPLOAD_DIR`

## 备注
- `DASHSCOPE_API_KEY` 不提供默认值，必须由外部环境注入。
