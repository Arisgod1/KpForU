# KpForU 核心技术概览（算法 / 模型 / 框架 / 协议 / 安全）

## 架构与组件
- **三端协同**：手机 Flutter、手表 Flutter、后端 FastAPI，REST `/v1` 统一入口；JWT 鉴权；云端存储与调度。
- **数据主路径**：手机配置 → 手表执行 → 云端存证 → 手机/手表回显；语音采集 → 云端转写 → 草稿 → 卡片；复习事件 → Leitner 算法 → 下一次复习时间。

## 算法与规则
- **Leitner 间隔算法**：间隔表 `{1:1, 2:2, 3:4, 4:7, 5:14}` 天；`done` 升盒（封顶 5）、`snooze` 延后 1/2/3 天；存 UTC 时间。实现于 [server/app/services/leitner.py](server/app/services/leitner.py)。
- **时间流（专注）**：模板驱动多阶段番茄流；阶段切换触发振动/全屏提示；前台服务保证计时不被系统杀死（手表端）。
- **AI 总结/转写**：调用 Qwen（通义千问）兼容 OpenAI API，摘要与语音转写逻辑在 [server/app/services/qwen_client.py](server/app/services/qwen_client.py)。

## 模型与依赖
- **后端**：FastAPI、SQLAlchemy 2.0、Pydantic v2、Alembic、python-jose、httpx、uvicorn。
- **AI**：DashScope/Qwen 兼容 OpenAI endpoint（`qwen3-omni-flash`，可换）；音频格式默认 wav，语音字段在 `/voice/drafts`。
- **手机端**：Flutter 3.10+；Provider + MultiProvider；`http`、`shared_preferences`、`file_picker`、`google_fonts`、`intl`、`uuid`。
- **手表端**：Flutter 3.10+；Riverpod；前台服务/通知/振动能力；同一 REST 客户端模式。

## 协议与接口
- **统一错误格式**：`{"error": {"code": str, "message": str, "details": object|null}}`；成功直接返回数据对象。
- **鉴权协议**：`Authorization: Bearer <token>`；Token 来源 `POST /v1/auth/token`（需先设备绑定 `POST /v1/devices/watch/register` + `POST /v1/binding/pair`）。
- **时间与时区**：数据库存 UTC；客户端请求带 `X-Client-Timezone`；`date` 查询参数为本地日期 `YYYY-MM-DD`，后端转换为 UTC 范围。
- **文件上传**：`POST /v1/voice/drafts` multipart，字段 `file`，大小默认 ≤20MB，存储于 `storage/voice/`，状态轮询 `GET /v1/voice/drafts/{id}`。

## 框架与代码结构
- **后端路由分层**：特性路由位于 `app/api/{auth,binding,timeflow,focus,cards,reviews,watch,voice,ai}.py`，统一聚合于 [server/app/api/__init__.py](server/app/api/__init__.py)；启动逻辑与异常处理在 [server/app/main.py](server/app/main.py)。
- **配置管理**：`pydantic-settings` 读取环境变量；关键项在 [server/app/core/config.py](server/app/core/config.py)（`DATABASE_URL`, `JWT_SECRET_KEY`, `DASHSCOPE_API_KEY`, `QWEN_MODEL`, `UPLOAD_MAX_MB`, `UPLOAD_DIR` 等）。
- **手机端状态管理**：`lib/src/app.dart` MultiProvider，`ProxyProvider` 注入 `ApiClient`；各特性 Store 位于 `lib/src/features/*/*_store.dart`；HTTP 封装在 [client/kpforu_phone/lib/src/core/api_client.dart](client/kpforu_phone/lib/src/core/api_client.dart)。
- **手表端结构**：`lib/src/features` 下按功能拆分；Riverpod 管理状态；前台服务确保计时与提醒可靠。

## 安全与合规
- **JWT 安全**：`HS256`，密钥由 `JWT_SECRET_KEY` 提供，默认 dev 值需生产覆盖；`JWT_EXPIRES_SECONDS` 默认 7 天。
- **上传限制**：`UPLOAD_MAX_MB` 控制文件大小；拒绝超限请求；上传目录启动时自动创建。
- **错误保护**：统一异常处理，未捕获异常返回 `internal_error`；避免泄露堆栈。
- **数据一致性**：手表离线操作本地存储，联网后重放；手机/手表均依赖云端为单一事实源。

## 预期与规划中的技术
- **双端语音记忆卡片（已落地基础版）**：手机端支持音频上传，后端调用 Qwen 进行转写并自动生成卡片 `front/back/tags` 草稿；失败时降级为可编辑占位草稿。
- **Agent 一键生成 PPT**：后端增加 Agent pipeline，基于卡片集/专注/复习日志生成可导出的 PPT（OpenAI 兼容接口 + 文档模板引擎）。
- **双端壁纸/表盘主题（已落地基础版）**：手机端支持本地图片/在线 URL/默认壁纸切换并持久化；手表端支持在线壁纸 URL 持久化，主页面实时生效。
- **通知与轻量提醒**：AI 总结生成后推送手表短提醒，手机展示完整内容。

## 2026-02 增量实现（本轮）
- **语音建卡增强**：`/v1/voice/drafts` 后台任务由 stub 升级为 Qwen Omni 语音理解，输出转写与卡片字段。
- **学习报告导出**：新增 `POST /v1/ai/exports/learning-pdf`，汇总时间流/卡片/专注/复习数据后调用大模型总结并输出 PDF。
- **前端体验优化**：手机端新增动态壁纸背景组件、统计数值动效、个性化入口；手表端新增壁纸设置入口。

## 快速运行与测试（摘要）
- 后端：`docker-compose up --build` 或 `uvicorn app.main:app --reload`（先 `pip install -r requirements.txt`）；迁移 `alembic upgrade head`；测试 `pytest`。
- 手机：`flutter pub get`；`flutter run --dart-define=BASE_URL=http://127.0.0.1:8000/v1`。
- 手表：同上，入口在手表工程；确保 BASE_URL 指向后端。
