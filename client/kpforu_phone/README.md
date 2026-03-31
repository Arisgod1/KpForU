# KpForU 手机端（Flutter）

手机端是主交互端，负责模板管理、复习卡片、语音草稿入口、个性化设置与学习总结导出。

## 运行方式
1. 进入目录：`cd client/kpforu_phone`
2. 安装依赖：`flutter pub get`
3. 启动应用：`flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1`

说明：
- `BASE_URL` 建议显式传入；默认按本地后端地址联调。
- 启动前请确保后端已运行。

## 功能模块
- 概览页：展示今日学习与复习摘要，支持触发周总结。
- 时间流页：模板创建/编辑/删除，支持直接开始专注流程。
- 复习页：到期卡片展示，支持“完成/稍后”与卡片编辑。
- 专注页：专注会话管理与历史记录。
- 个性化页：
  - 本地/在线壁纸切换
  - 语音上传生成卡片草稿
  - 一键导出学习总结 PDF

## 已对接后端接口
- 绑定鉴权：`/v1/binding/pair`、`/v1/auth/token`
- 时间流：`/v1/timeflows/templates`
- 专注：`/v1/focus/sessions`
- 复习：`/v1/reviews/due`、`/v1/reviews/events`
- 卡片：`/v1/cards`
- 语音：`/v1/voice/drafts`、`/v1/voice/drafts/{draft_id}`
- AI：`/v1/ai/summaries/daily`、`/v1/ai/summaries/weekly`
- 导出：`/v1/ai/exports/learning-pdf`

## 统一等待策略（语音与导出）

- 配置文件：`lib/src/core/ai_wait_policy.dart`
- 统一参数：
  - `requestTimeout`：语音上传请求超时（默认 60s）
  - `pollInterval`：语音草稿状态轮询间隔（默认 2s）
  - `pollTimeout`：语音处理总等待时长（默认 90s）
  - `pollRequestTimeout`：单次轮询请求超时（默认 15s）
  - `exportRequestTimeout`：学习总结 PDF 导出超时（默认 120s）

说明：
- 语音链路为“上传 + 轮询回调完成”模式，不再只按上传成功判定最终成功。
- 若网络较慢，可先增大 `pollTimeout` 与 `exportRequestTimeout` 再联调。

## 质量状态
- 静态检查：`flutter analyze` -> `No issues found!`（2026-03-27）

## 后续可扩展
- 真机录音替代文件选择上传
- 导出 PDF 模板增强（图表/字体）
- 壁纸与偏好设置多端同步
