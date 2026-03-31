# KpForU 手表端（Flutter）

KpForU 手表端用于专注计时、复习操作确认与语音建卡上传，重点优化了圆屏小尺寸可触达性和手机/云端同步稳定性。

## 快速启动

1. 进入目录：`client/kpforu_watch`
2. 安装依赖：`flutter pub get`
3. 运行：`flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1`

## 本次版本关键行为（已更新）

- 专注页按钮流程：
  - 初始状态仅显示一个居中绿色开始按钮。
  - 开始后显示两个按钮：暂停/继续、下一阶段。
- 暂停行为：
  - 暂停只暂停倒计时，不会触发“保存记录确认”。
- 结束确认行为：
  - 仅在完整流程结束（阶段推进到终点）后触发“是否保存记录”确认。
  - 取消保存后恢复到初始状态（第一阶段、未开始）。

## 圆屏适配策略（OPPO 圆表方向）

- 统一按最短边百分比计算安全边距（约 8%），避免边缘按钮难以点击。
- 专注页顶部按钮、中心内容、确认弹层均向安全区内收。
- 结束确认弹层改为居中圆形操作区，确认/取消按钮上移，避免底部盲区。
- 复习卡片页与历史页按圆屏安全边距做布局，减少内容被圆角截断。

## Windows 预览说明

- 桌面预览已启用固定正方形窗口（默认 `466x466`，不可拉伸），用于稳定模拟手表可视区。
- 如果修改了窗口参数，需“停止后重新 `flutter run`”，仅热重载不会完全刷新窗口尺寸。

## 核心功能

- 专注时间流：开始/暂停/继续/跳过阶段；循环（cycles/repeat/until_time）切换。
- 数据记录：会话结束后一次性上传；支持“手动确认再保存”。
- 复习中心：翻卡、完成/稍后、到期状态展示。
- 语音建卡：录音上传到 `/v1/voice/drafts`，由后端异步生成草稿卡片。
- 设备绑定：绑定码上传 + 轮询鉴权令牌。
- 手表壁纸同步：读取手机端下发的手表壁纸 URL（`/v1/watch/wallpaper`）。

## 统一等待策略（语音回调）

- 语音上传不再“仅上传成功即成功”，而是上传后轮询 `GET /v1/voice/drafts/{draft_id}`，等待后端异步处理完成。
- 统一参数文件：`lib/src/core/ai_wait_policy.dart`
  - `requestTimeout`：上传请求超时（默认 60s）
  - `pollInterval`：轮询间隔（默认 2s）
  - `pollTimeout`：轮询总时长（默认 90s）
  - `pollRequestTimeout`：单次轮询超时（默认 15s）

## 主要界面与交互

- 专注页：
  - 左上角：进入复习页；右上角：菜单（模板/历史/设置）。
  - 中心：阶段名、循环信息、倒计时、进度环。
  - 控制区：初始单按钮；开始后双按钮（暂停/继续 + 下一阶段）。
  - 结束确认：圆形弹层确认/取消。
- 绑定页：
  - 展示绑定码，按钮为圆形“上传”“绑定完成”，适配圆屏安全区。
- 语音页：
  - 中心主按钮随状态切换（录音/停止/上传），错误信息放入底部安全区。

## 后端接口对接

- 鉴权/绑定：
  - `POST /v1/devices/watch/register`
  - `POST /v1/binding/pair`
  - `POST /v1/auth/token`
- 专注：
  - `POST /v1/focus/sessions`
  - `GET /v1/focus/sessions`
  - `DELETE /v1/focus/sessions/{session_id}`
- 模板：
  - `GET /v1/timeflows/templates`
  - `DELETE /v1/timeflows/templates/{template_id}`
- 复习：
  - `GET /v1/reviews/due?date=YYYY-MM-DD`
  - `POST /v1/reviews/events`
  - `GET /v1/watch/review/metrics`
- 语音：
  - `POST /v1/voice/drafts`
  - `GET /v1/voice/drafts/{draft_id}`
- 手表壁纸：
  - `GET /v1/watch/wallpaper`
  - `PUT /v1/watch/wallpaper`

## 上传负载（专注会话）

- 路径：`POST /v1/focus/sessions`
- 关键字段：
  - `client_generated_id`
  - `template_snapshot`
  - `started_at` / `ended_at`
  - `ended_reason`（`natural` / `user_ended`）
  - `ended_phase_index`
  - `manual_confirm_required`
  - `saved_confirmed`

实现参考：`lib/src/features/focus/focus_store.dart`。

## 常见问题

- 语音上传 404：确认路径使用 `/v1/voice/drafts`，不要使用旧路径 `voice-card`。
- 语音处理等待超时：可先在语音页重试，或适当调大 `lib/src/core/ai_wait_policy.dart` 中的 `pollTimeout`。
- 未绑定无法上传：可离线计时，但云端请求会失败，先在绑定页完成绑定。
- 小屏触控困难：当前版本已将确认弹层与主要按钮提升至圆屏安全区。

