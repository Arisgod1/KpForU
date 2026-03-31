# KpForU 手机端（Flutter）

> **主交互端**：模板管理 × 复习卡片 × 语音建卡 × 学习总结

手机端是 KpForU 的核心交互界面，用户在这里完成：
- 📝 时间流模板的创建和启动
- 📚 复习卡片的完成和调度管理
- 🎤 语音快速建卡
- 📊 学习数据汇总和 PDF 导出

## 🚀 快速开始

### 环境要求
- Flutter 3.10+ ([下载安装](https://flutter.dev/docs/get-started/install))
- Dart 3.0+
- 后端服务已启动（详见 [server/README.md](../../server/README.md)）

### 运行步骤

```bash
# 1. 进入项目目录
cd client/kpforu_phone

# 2. 安装依赖
flutter pub get

# 3. 启动应用
# Windows 模拟器
flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1

# 或连接到实机（Android/iOS）
flutter run -d <device_id> --dart-define=BASE_URL=http://127.0.0.1:8000/v1
```

**说明**：
- `BASE_URL` 需要指向后端 API 地址（开发环境通常是 `http://127.0.0.1:8000/v1`）
- 如果不指定 `BASE_URL`，应用会从编译时配置读取
- 首次启动会在 `lib/src/core/env.dart` 中查找默认值

### 代码风格检查

```bash
# 静态分析
flutter analyze

# 代码格式化
flutter format lib/

# 运行单元测试
flutter test
```

---

## 📱 功能模块详解

### 1. **Dashboard / 概览页面**

**路由**：`/dashboard`

**主要功能**：
- 📊 **今日学习统计**
  - 专注时长（按科目分类）
  - 复习卡片完成数和掌握度
  - 新增卡片数量

- 💡 **AI 学习总结**
  - 日报：显示当天关键数据和 AI 建议
  - 周报：周趋势分析和长期进度

- ⚡ **快捷操作**
  - "立即开始"专注（在手表上）
  - "开始语音建卡"
  - "导出学习报告"

**核心代码**：
- `lib/src/features/dashboard/dashboard_store.dart` — 状态管理
- `lib/src/features/dashboard/dashboard_page.dart` — UI 组件

**数据流**：
```
DashboardStore.fetch()
  ├─ GET /v1/focus/sessions (今日专注数据)
  ├─ GET /v1/reviews/due (待复习卡片)
  ├─ GET /v1/ai/summaries/daily (日报)
  └─ GET /v1/ai/summaries/weekly (周报)
```

---

### 2. **TimeFlow / 时间流模板**

**路由**：`/timeflow`

**主要功能**：
- ➕ **创建模板**
  - 输入模板名称、科目标签
  - 添加多个学习阶段（段名、时长）
  - 保存到云端

- ✏️ **编辑和删除**
  - 修改已有模板
  - 删除不再使用的模板

- ▶️ **快速启动**
  - 选择模板 → 推送到手表 → 手表自动开始倒计时

---

### 3. **Reviews / 复习卡片列表**

**路由**：`/reviews`

**主要功能**：
- 📋 **展示到期卡片**
- ✅ **复习操作**（完成/延期/删除）
- 🔄 **下拉刷新**

---

### 4. **Voice / 语音建卡**

**路由**：`/voice`

**核心流程**：
```
录音 → 上传(WAV) → 轮询进度 → 显示生成卡片 → 用户编辑/确认
```

**技术亮点**：
- 🎙️ WAV 格式(16kHz单声道)
- 🤖 Qwen-Omni-Flash 多模态模型
- 💾 智能缓存（数据不变则命中缓存）

---

### 5. **Personalization / 个性化设置**

**功能**：
- 🖼️ 壁纸管理（本地/在线）
- 📊 学习输出导出（PDF）
- ⌚ 设备管理（与手表配对）

---

## 🔌 关键后端接口

| 端点 | 功能 |
|-----|------|
| `GET /v1/reviews/due` | 获取到期卡片 |
| `POST /v1/reviews/events` | 上报复习操作 |
| `POST /v1/voice/drafts` | 上传语音 |
| `GET /v1/ai/summaries/daily` | 获取日报 |
| `POST /v1/ai/exports/learning-pdf` | 导出PDF |

---

## ⚙️ 配置说明

### 基础配置
**文件**：`lib/src/core/env.dart`

```dart
const String baseUrl = 'http://127.0.0.1:8000/v1';
```

### 超时参数
**文件**：`lib/src/core/ai_wait_policy.dart`

```dart
class AiWaitPolicy {
  static const int requestTimeout = 60;       // 上传超时
  static const int pollInterval = 2;          // 轮询间隔
  static const int pollTimeout = 90;          // 总超时
  static const int exportRequestTimeout = 120; // PDF导出超时
}
```

---

## 📊 质量保证（2026-03-27）

```bash
$ flutter analyze
No issues found! ✓
```

---

## 📚 完整文档

- 📖 **项目主README** → [../../README.md](../../README.md)
- 🔧 **后端文档** → [../../server/README.md](../../server/README.md)
- ⌚ **手表端文档** → [../kpforu_watch/README.zh-CN.md](../kpforu_watch/README.zh-CN.md)
- 🎬 **视频演示稿** → [../../docs/VIDEO_SCRIPT_DUAL_DETAILED.md](../../docs/VIDEO_SCRIPT_DUAL_DETAILED.md)
