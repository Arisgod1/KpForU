# KpForU 手表端（Flutter）

KpForU 手表端主要用于专注计时、复习提醒确认与快速语音卡片创建，强调低功耗、最少交互和与手机/云端的可靠同步。

## 快速启动

1. 进入目录：`client/kpforu_watch`
2. 安装依赖：`flutter pub get`
3. 运行：`flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1`

## 核心功能

- 专注时间流：前台服务保持倒计时，支持开始/暂停/跳过阶段/结束会话；循环（cycles/repeat/until_time）精确切换。
- 阶段提醒：每个阶段切换触发本地通知与震动；可选学习阶段间隔震动。
- 数据记录：完整会话结束后一次性上传专注记录；支持“手动确认再保存”。
- 复习提醒中心：展示今日到期数量与下一次时间；卡片正反面翻转；“完成/稍后”操作并同步云端。
- 语音卡片：录音（≤30s / ≤500KB）并上传，失败提示与重试；草稿删除手势。
- 设备绑定与鉴权：生成绑定码，上传后持久化令牌；未绑定下离线可用（不上传）。

## 运行与开发

- 依赖：Flutter 3.x；Riverpod 状态管理。
- 手表端入口：`lib/src/features/home/home_page.dart`。
- 后端地址：`lib/src/core/env.dart` 中 `BASE_URL`（建议通过 `--dart-define` 覆盖）。

## 主要界面与交互

- 专注页：
  - 左上角：进入记忆卡片按钮；右上角：菜单（模板/历史/设置）。
  - 中心：当前阶段名、循环信息、倒计时与进度环；底部：开始/暂停/下一个。
  - 结束确认：若开启“手动确认”，弹出小屏适配的 5 秒倒计时卡片；确认后上传，取消则保留本地状态。
- 记忆卡片页：
  - 顶部 AppBar：标题与“手动确认”开关（控制专注记录是否需确认）。
  - 卡片：点击翻转正反面；“完成/稍后”按钮始终可触达，正文可滚动适配小屏。

## 后端接口对接

- 专注记录
  - 创建：`POST /v1/focus/sessions`
  - 列表：`GET /v1/focus/sessions`
  - 删除：`DELETE /v1/focus/sessions/{session_id}`
- 时间流模板
  - 列表：`GET /v1/timeflows/templates`
  - 删除：`DELETE /v1/timeflows/templates/{template_id}`
- 复习
  - 今日待复习：`GET /v1/reviews/due?date=YYYY-MM-DD`
  - 上报事件：`POST /v1/reviews/events`（完成/延期）

## 上传负载（专注结束）

- 路径：`POST /v1/focus/sessions`
- 字段：
  - `client_generated_id`：前端生成的 10 位随机 ID（幂等）
  - `template_snapshot`：`TimeFlowTemplate.toCreatePayload()`（name/phases/loop）
  - `started_at` / `ended_at`：ISO8601
  - `ended_reason`：`natural` 或 `user_ended`
  - `ended_phase_index`：最终阶段索引
  - `manual_confirm_required`：是否启用手动确认
  - `saved_confirmed`：是否已确认保存

实现参考：`lib/src/features/focus/focus_store.dart`。

## 状态管理（Riverpod）

- 专注：`focusStoreProvider` 管理模板、当前阶段、循环、会话开始时间与上传标志；监听服务事件驱动倒计时。
- 复习：`reviewStoreProvider` 管理今日待复习列表；操作乐观更新并调用事件接口。
- 服务：`focusServiceProvider` 提供倒计时后台服务（前台服务约束遵循 Wear OS/watchOS 指南）。

## 低功耗策略

- 合并唤醒与震动；学习阶段间隔震动避免频繁唤醒；网络上传尽量批处理。
- UI 空闲 30fps；黑色背景优先，适配 OLED 减少功耗。

## 测试与质量

- 计时状态机：使用假时间源的单元测试确保阶段与循环精确。
- 可访问性：建议在真机验证震动强度与提示对比度。

## 目录结构

- `lib/src/features/focus/` 专注页与状态
- `lib/src/features/review/` 复习页与状态
- `lib/src/features/voice/` 语音卡片页与状态
- `lib/src/services/` 倒计时服务等
- `lib/src/core/models/` 数据模型

## 常见问题

- 404：确保上传路径为 `/v1/focus/sessions`，不要用 `/focus/records`。
- 未绑定：允许离线计时与本地草稿，但云端上传会失败；先在绑定页完成设备绑定。
- 小屏溢出：卡片正文支持滚动；确认覆盖层采用自适应方形卡片，避免底部溢出。

