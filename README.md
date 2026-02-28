# KpForU

KpForU 是一个“手机 + 手表 + 云端 AI”协同学习系统，面向专注计时、间隔复习和学习总结三个核心场景。

## 项目组成
- 手机端：Flutter，主交互入口（时间流模板、复习卡片、个性化、导出 PDF）。
- 手表端：Flutter，轻交互入口（专注计时、复习提醒确认、语音采集）。
- 后端：FastAPI + SQLAlchemy，提供设备绑定、鉴权、数据同步、AI 接口。

## 当前已实现能力
- 时间流：模板创建/更新/删除、专注会话记录。
- 复习：到期卡片查询、完成/延期事件上报。
- 语音建卡：上传音频后由大模型生成卡片草稿。
- AI 总结：日报/周报；学习数据汇总导出 PDF（手机端）。
- 壁纸与视觉：手机端多页面统一壁纸与玻璃质感样式。

## 目录结构
- `client/kpforu_phone`：手机端工程。
- `client/kpforu_watch`：手表端工程。
- `server`：后端工程。
- `docs`：技术文档与阶段执行记录。

## 快速联调（本地）
1. 启动后端（见 `server/README.md`）。
2. 启动手机端：
   - `cd client/kpforu_phone`
   - `flutter pub get`
   - `flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1`
3. 启动手表端：
   - `cd client/kpforu_watch`
   - `flutter pub get`
   - `flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1`

## 质量状态（2026-02-28）
- 手机端静态检查：`flutter analyze` -> `No issues found!`
- 后端流程自测：语音草稿接口、学习总结 PDF 导出接口已通过自测。
- CI 门禁：`.github/workflows/quality-gate.yml`（后端 `pytest` + 手机端 `flutter analyze`）。

## 参考文档
- 后端说明：`server/README.md`
- 手机端说明：`client/kpforu_phone/README.md`
- 手表端说明：`client/kpforu_watch/README.zh-CN.md`
- 执行记录：`docs/task_execution_2026-02-28.md`