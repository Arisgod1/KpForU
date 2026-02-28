# 任务执行记录（2026-02-28）

## 一、任务逻辑拆分
1. **前端视觉与体验升级（双端）**
   - 手机端：统一动态壁纸背景、统计卡片动效、个性化入口。
   - 手表端：支持壁纸 URL 设置并持久化。
2. **语音输入生成卡片（后端能力 + 手机接入）**
   - 上传音频 -> 后台调用 Qwen Omni -> 生成 `transcript/front/back/tags` -> 自动建草稿卡片。
3. **手机端一键导出学习总结 PDF**
   - 汇总当前用户所有时间流、卡片、专注、复习数据 -> 调用大模型总结 -> 生成 PDF 并回传下载。
4. **文档与测试闭环**
   - 每个阶段完成后更新技术文档；新增/更新接口测试。

## 二、本次已完成
### A. 前端美化与双端壁纸
- 手机端新增：
  - `lib/src/core/wallpaper_store.dart`
  - `lib/src/core/wallpaper_background.dart`
  - `lib/src/features/dashboard/personalize_page.dart`
- 手机端改造：
  - `dashboard_page.dart`：增加个性化入口、统计数值动画。
  - `timeflow_page.dart`/`reviews_page.dart`：接入动态壁纸背景。
  - `voice_capture_page.dart`：修复上传字段为 `file`。
- 手表端新增：
  - `lib/src/core/wallpaper_store.dart`
- 手表端改造：
  - `providers.dart`：注入壁纸 Provider。
  - `focus_page.dart`：应用壁纸背景，设置菜单新增壁纸 URL 配置与重置。

### B. 语音输入添加卡片
- 后端升级：
  - `server/app/services/qwen_client.py`：新增音频输入 -> 卡片字段生成逻辑。
  - `server/app/services/voice.py`：后台任务替换 stub，调用 Qwen 自动生成 `front/back/tags`。
  - `server/app/api/voice.py` / `server/app/schemas/voice.py`：补充 `transcript_text` 返回字段。

### C. 手机端 PDF 导出
- 后端新增：
  - `server/app/services/learning_export.py`
  - 新接口 `POST /v1/ai/exports/learning-pdf`（位于 `server/app/api/ai.py`）
- 手机端接入：
  - `ApiClient.postBytes()` 支持二进制下载。
  - 个性化页面增加“一键导出学习总结 PDF”，保存到应用文档目录。

### D. 安全与配置
- `server/app/core/config.py`：移除硬编码 DashScope Key 默认值，改为仅环境变量配置。

## 三、接口自测与测试结果
### 已添加
- `server/tests/test_flow.py` 新增 `POST /v1/ai/exports/learning-pdf` 断言：
  - 返回 `application/pdf`
  - 内容以 `%PDF` 开头。

### 实际执行结果（2026-02-28）
1. 环境：`conda activate kpforu-server`
2. 依赖安装：`pip install -r server/requirements.txt`（包含 `reportlab`）
3. 后端流程测试：
   - 命令：`pytest tests/test_flow.py -q`
   - 结果：`1 passed`
4. 新接口自测（TestClient 脚本）：
   - `POST /v1/voice/drafts` -> `201`
   - `GET /v1/voice/drafts/{id}` -> `200`，并返回 `transcript_text`
   - `POST /v1/ai/exports/learning-pdf` -> `200`，`content-type=application/pdf`，内容以 `%PDF` 开头

### 本轮联调修复项
- 修复 UUID 兼容问题：
  - `server/app/core/security.py`（token 中 `user_id` 转 UUID）
  - `server/app/schemas/review.py`（`ReviewEventCreate.card_id` 改为 UUID）
  - `server/app/services/voice.py`（后台任务 `draft_id` 转 UUID）
- 修复手表指标接口时区问题：
  - `server/app/api/watch.py`（处理 SQLite 返回的 naive datetime）
- 修复双端前端静态问题：
  - 手表端去除无用导入、修正错误 `@override`、更新 `widget_test.dart`
  - 手机端去除未使用私有方法 `_showCreateSheet`

### 建议执行（本地）
1. 后端依赖安装：`pip install -r server/requirements.txt`
2. 启动后端：`uvicorn app.main:app --reload`（在 `server` 目录）
3. 运行测试：`pytest server/tests/test_flow.py`
4. 手机端：
   - `flutter pub get`（`client/kpforu_phone`）
   - 进入“个性化与导出”页面测试：
     - 本地壁纸切换
     - 在线壁纸 URL
     - 语音上传建卡
     - PDF 导出
5. 手表端：
   - `flutter pub get`（`client/kpforu_watch`）
   - Focus 菜单 -> Wallpaper URL 测试背景生效。

## 四、当前状态
- 已完成任务 1、2、3 的实现、文档更新与后端测试/接口自测。
- 下一步可继续：
  - 完善手机端实时录音（不仅文件上传）
  - PDF 模板美化（中文字体、图表）
  - 壁纸双端云同步（同账号自动同步）

## 五、继续优化（保持功能与尺寸规格不变）
### 本轮目标
- 仅做非功能性优化，不改页面功能、不改布局尺寸与交互流程。
- 重点清理 Flutter 静态分析告警（异步 `BuildContext` 使用与弃用 API）。

### 本轮改动
- 弃用 API 清理：
  - 将 `withOpacity` 替换为 `withValues(alpha: ...)`。
  - `WillPopScope` 迁移为 `PopScope`，保持原返回拦截逻辑。
  - 移除主题中已弃用 `ColorScheme.background` 字段。
- 异步上下文安全优化：
  - 在异步间隙后补充 `context.mounted`/`mounted` 安全关口。
  - 将部分 `ScaffoldMessenger`、`Navigator`、`Store` 引用前置缓存，避免 await 后直接访问旧 `context`。
  - 局部刷新逻辑改为直接调用已缓存 Store，避免跨 async gap 传递 `BuildContext`。

### 涉及文件（手机端）
- `client/kpforu_phone/lib/src/features/dashboard/dashboard_page.dart`
- `client/kpforu_phone/lib/src/features/dashboard/personalize_page.dart`
- `client/kpforu_phone/lib/src/features/focus/focus_page.dart`
- `client/kpforu_phone/lib/src/features/reviews/reviews_page.dart`
- `client/kpforu_phone/lib/src/features/timeflow/timeflow_page.dart`
- `client/kpforu_phone/lib/src/features/timeflow/timeflow_run_page.dart`
- `client/kpforu_phone/lib/src/features/voice/voice_capture_page.dart`
- `client/kpforu_phone/lib/src/navigation/root_shell.dart`
- `client/kpforu_phone/lib/src/theme/app_theme.dart`

### 验证结果（2026-02-28）
- 执行：`flutter analyze`（目录：`client/kpforu_phone`）
- 最终结果：`No issues found!`

## 六、继续优化（二）：工程稳定性与交付质量
### 本轮目标
- 提升本地启动稳定性（尤其是后端环境不一致时）。
- 建立最小 CI 质量门禁，降低回归风险。
- 固化 VS Code 的 Python 环境选择，减少重复激活成本。

### 本轮改动
1. 后端启动脚本
   - 新增：`server/scripts/start_backend.ps1`
  - 补充：`server/scripts/start_backend.bat`（可双击/命令行启动，内部转调 ps1）
   - 能力：
     - 支持 `-BindHost` / `-Port` 参数启动
     - 支持 `-UseSqlite` 快速回退 SQLite
     - 自动检测并优先使用 `kpforu-server` 解释器
     - 给出 conda 环境友好提示

2. CI 质量门禁
   - 新增：`.github/workflows/quality-gate.yml`
   - 覆盖：
     - 后端：`pytest tests/test_flow.py -q`
     - 手机端：`flutter analyze`

3. 工作区环境固化
   - 更新：`.vscode/settings.json`
   - 固定：`python.defaultInterpreterPath = C:/Users/wwwsh/.conda/envs/kpforu-server/python.exe`
   - 启用：`python.terminal.activateEnvironment = true`

4. README 同步
   - 更新：`README.md`、`server/README.md`
   - 补充了 CI 说明与后端一键启动脚本说明。

### 本轮验证结果（2026-02-28）
- 后端测试（conda 环境解释器）：
  - 命令：`C:/Users/wwwsh/.conda/envs/kpforu-server/python.exe -m pytest tests/test_flow.py -q`
  - 结果：`1 passed`
- 手机端静态分析：
  - 命令：`flutter analyze`（`client/kpforu_phone`）
  - 结果：`No issues found!`
- 启动脚本冒烟验证：
  - 命令：`powershell -ExecutionPolicy Bypass -File .\server\scripts\start_backend.ps1 -UseSqlite -BindHost 127.0.0.1 -Port 8010`
  - 结果：成功拉起 Uvicorn 并进入监听状态。

### 本轮补充（BAT 入口）
- 新增：`server/scripts/start_backend.bat`
- 用法：`server\scripts\start_backend.bat -UseSqlite -BindHost 127.0.0.1 -Port 8010`

## 七、CI 故障修复（2026-02-28）
### 问题现象
1. 后端 CI 失败：`/v1/voice/drafts` 上传时报 `FileNotFoundError: storage/voice/sample.wav`。
2. 手机端 CI 失败：`flutter analyze` 报 `asset_does_not_exist`（`lib/src/asserts/background.jpg`）。

### 修复措施
1. 后端修复（根因修复）
  - 文件：`server/app/api/voice.py`
  - 变更：在写入上传文件前执行 `os.makedirs(settings.upload_dir, exist_ok=True)`，确保目录存在。

2. 前端修复（资源补全）
  - 文件：`client/kpforu_phone/lib/src/asserts/background.jpg`
  - 变更：补齐并纳入版本管理，确保 CI 环境可找到声明的资源文件。

### 验证结果
- 后端：`C:/Users/wwwsh/.conda/envs/kpforu-server/python.exe -m pytest tests/test_flow.py -q` -> `1 passed`
- 手机端：`flutter analyze`（`client/kpforu_phone`）-> `No issues found!`
