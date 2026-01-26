# KpForU 手机端（Flutter）

> 状态：已接入后端 API（绑定/鉴权、时间流模板、复习待办、语音草稿上传），需配置 BASE_URL 与后端联通。

## 快速启动
1. 安装 Flutter 3.10+ 环境。
2. 进入 `client/kpforu_phone`：
	```bash
	flutter pub get
	flutter run --dart-define=BASE_URL=http://127.0.0.1:8000/v1
	```
	- 如需指向线上，替换 BASE_URL。

> BASE_URL 通过 `--dart-define` 注入，默认为 `http://127.0.0.1:8000/v1`。

## 界面模块
- **概览**：展示今日待复习数量、时间流模板数、AI 简要总结（AI 区块仍为占位）。
- **时间流模板**：从 `/timeflows/templates` 拉取，支持新增、删除（POST/DELETE）。
- **复习待办**：从 `/reviews/due` 获取到期卡片；“完成/稍后”调用 `/reviews/events`（done/snooze）。
- **语音草稿**：选择本地音频文件后，调用 `/voice/drafts` 上传，轮询 `/voice/drafts/{id}` 获取状态。 

## 接口对照与对接计划（后端 `/v1`）
| 模块 | 应用端需求 | 后端接口 | 当前状态 | 备注 |
| --- | --- | --- | --- | --- |
| 设备绑定/鉴权 | 获取 Token | `POST /auth/token`（绑定后） | 已实现 | Token 持久化 shared_preferences |
| 绑定配对 | 输入绑定码完成配对 | `POST /binding/pair` | 已实现 | 需提前完成手表 `watch/register` |
| 时间流模板 | 列表/新增/删除 | `GET/POST/DELETE /timeflows/templates` | 已实现 | 更新/分页待补充 |
| 专注记录 | 上传结束记录 | `POST /focus/sessions` | 已实现 | 手表端主用，手机端可做历史查询 |
| 复习待办 | 获取到期卡片 | `GET /reviews/due` | 已实现 | 传 `date=YYYY-MM-DD` |
| 复习事件 | done/snooze 提交 | `POST /reviews/events` | 已实现 | 复习页按钮已调用 |
| 卡片管理 | 创建/更新/列表 | `POST /cards`，`PUT /cards/{id}` | 已实现 | 手机端卡片编辑后续迭代 |
| 手表指标 | 今日计划/已完成 | `GET /watch/review/metrics` | 已实现 | 可在概览页显示 |
| 语音草稿 | 上传录音/查询结果 | `POST /voice/drafts`，`GET /voice/drafts/{id}` | 已实现 | 通过文件选择器上传 multipart 并轮询 |
| AI 总结 | 每日/每周总结 | `POST /ai/summaries/daily`，`POST /ai/summaries/weekly` | 已实现 | 概览页留有占位 |

## 下一步对接建议
1) 覆盖剩余接口：卡片 CRUD、手表指标、AI 总结、专注记录列表。
2) 增加错误态展示细化（字段校验）与重试策略；补充分页游标支持。
3) 录音采集改为真机录音 + 权限申请，当前为文件选择上传。
4) 视图与 Store 补充缓存策略（如本地 Room/SQLite）与离线提示。
