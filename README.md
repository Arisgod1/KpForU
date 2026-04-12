# KpForU - 双端协同专注学习系统

> 一个集**专注计时 × 间隔复习 × AI学习总结**于一身的手机+手表+云端协同系统
> 
> *使用通义千问大模型进行智能语音转写和学习数据分析，采用Leitner算法优化复习调度*

## 📱 项目概述

**KpForU** 是为有学习目标的学生和专业人士设计的全栈学习工具：

- 📱 **手机端（Flutter）**：完整的学习系统入口——时间模板管理、复习卡片、语音建卡、学习总结导出
- ⌚ **手表端（Flutter）**：轻量交互——专注计时、复习提醒、语音采集（支持圆屏适配）
- ☁️ **后端服务（FastAPI）**：云端数据同步、设备鉴权、AI大模型接入（通义千问）

### 核心解决的问题

| 场景 | 解决方案 |
|------|-------|
| **碎片化学习** | 时间流模板系统：将学习分解为多个专注阶段，支持不同科目/任务的定制流程 |
| **遗忘曲线问题** | Leitner 间隔复习算法：自动计算复习间隔（1/2/4/7/14天），根据掌握程度动态调整 |
| **重复记卡浪费时间** | AI 语音建卡：语音输入→通义千问转写+理解→自动生成卡片（问题+答案），1句话生成1张卡 |
| **学习效率追踪困难** | AI 学习总结：日报/周报自动统计专注时长、复习次数、掌握进度，支持PDF导出 |
| **手表端独立操作** | 前台服务保障：手表计时不被系统杀死，离线事件本地缓存，自动同步到云端 |

---

## 🎯 核心功能详解

### 1️⃣ **时间流模板系统** (Dashboard → TimeFlow)

**场景**：早上30分钟复习英语单词

```
创建模板：
  - 第1段：预热 (2分钟)   ← 快速回顾之前学的内容
  - 第2段：主学 (20分钟)  ← 集中学习新单词
  - 第3段：复习 (5分钟)   ← 测试记忆
  - 第4段：反思 (3分钟)   ← 记录难点
```

**特性**：
- ✅ 支持多个模板（英语、数学、编程等）
- ✅ 模板快速开始 → 进入手表专注计时
- ✅ 会话自动记录为数据点，用于生成学习图表
- ✅ 手表端支持全屏倒计时 + 振动提醒 + 段间语音通知

---

### 2️⃣ **智能复习卡片** (Reviews / Cards)

**算法基础**：Leitner Box 间隔重复系统
```
第1遍：1天后   (记忆新鲜度最高时)
第2遍：2天后
第3遍：4天后
第4遍：7天后
第5遍：14天后  (长期记忆稳定)
```

**交互流程**：
```
手机端复习页 ← (实时同步) → 手表端复习待办
   ↓
选择卡片 → 点击"完成" → 升盒 (例: Box1→Box2)
         → 点击"稍后" → 延期1/2/3天
         → 点击"删除" → 从系统移除
   ↓
后端自动计算next_review_at，用户下次打开自动显示该卡片
```

**智能特性**：
- 🧠 Leitner 算法自动调度，不需手动安排
- 📊 掌握度追踪：完成次数越多→间隔越长
- 🎯 优先级排序：按到期时间优先展示最应该复习的卡片

---

### 3️⃣ **AI 语音建卡** (Voice Recording & Draft)

**使用场景**：面试准备，1分钟语音速记

```
终端用户：
  "我要给宫本武藏画传记，他的人生经历是..."
  (边说边走，共录了90秒音频)
  
APP动作：
  ↓
  上传to后端 (WAV格式，自动压缩到16kHz单声道)
  ↓
  后端调用通义千问3-Omni-Flash
  ├─ 转写音频 → "我要给宫本武藏画传记，他的人生经历是..."
  ├─ 提取核心 → "宫本武藏的人生经历"
  └─ 生成卡片草稿：
      Front: "日本剑客宫本武藏的主要人生经历有哪些？"
      Tags: ["历史", "日本文化", "人物传记"]
```

**技术亮点**：
- 🎙️ 支持m4a/wav双格式，自动标准化（16kHz单声道）
- 🤖 使用Qwen3-Omni-Flash多模态模型（业界先进，价格低廉）
- 💾 智能缓存：同一天数据不变 → 不重复调用LLM → 省钱
- 📄 支持编辑：AI生成的卡片可手动编辑后确认

**处理流程**（后台异步）：
```
① 上传音频 → 返回draft_id (立即返回)
② 客户端轮询 /voice/drafts/{id} status字段
   - "processing" → 继续等待
   - "done" → 显示生成的卡片
   - "failed" → 回退到可编辑占位符
③ 用户确认or编辑 → 转为Card对象，进入复习系统
```

---

### 4️⃣ **AI 学习总结** (Daily/Weekly Summary)

**日报示例**：
```
2026年3月27日 学习总结

📊 今日数据
  ├─ 专注时长：145分钟 (地理、英语、编程)
  ├─ 复习卡片：32张完成，8张延期
  └─ 新增卡片：5张 (4张语音建卡，1张手动)

🎯 学习进度
  ├─ 地理：完成度 78% ↑5%
  ├─ 英语：完成度 92% (2张升到Box5)
  └─ 编程：完成度 65% ↑12%

💡 AI建议
  └─ "英语单词复习成效显著，今日升盒率92%属于高效率。
      建议继续维持当前学习强度，可考虑增加编程的复习频次。"

--- 周报同理，展示本周趋势
```

**技术细节**：
- 📈 后端并行收集：专注时长、卡片完成数、掌握度变化
- 🧠 调用Qwen-Plus文本模型进行分析和建议
- 💾 缓存策略：同一天数据未变化 → 返回缓存报告（不调LLM）
- 📄 支持导出为PDF：包含图表+详细数据

---

## 🏗️ 系统架构

### 三层架构设计

```
┌──────────────────────────────────────────────────┐
│  Front Layer: 双端 Flutter                         │
├──────────────────────────────────────────────────┤
│ 手机端 (kpforu_phone)     │  手表端 (kpforu_watch)  │
│ ├─ Dashboard              │ ├─ Focus Timer         │
│ ├─ TimeFlow (模板)        │ ├─ Reviews (待办)      │
│ ├─ Reviews (卡片)         │ ├─ Voice Record        │
│ ├─ Voice (建卡)           │ └─ Watch Settings      │
│ ├─ Personalization        │                        │
│ └─ Export PDF             │                        │
└──────────────────────────────────────────────────┘
              ↓ REST API (JSON) ↓
┌──────────────────────────────────────────────────┐
│  API Layer: FastAPI (server/app/api)             │
├──────────────────────────────────────────────────┤
│ • /v1/auth          → JWT鉴权                    │
│ • /v1/timeflows     → 模板CRUD                   │
│ • /v1/focus         → 专注会话记录               │
│ • /v1/reviews       → 复习事件                   │
│ • /v1/cards         → 卡片CRUD                   │
│ • /v1/voice/drafts  → 语音处理（异步+轮询）     │
│ • /v1/ai/summaries  → 日/周报告                  │
│ • /v1/ai/exports    → PDF导出                    │
│ • /v1/watch         → 手表专用端点               │
└──────────────────────────────────────────────────┘
       ↓ SQLAlchemy ORM ↓       ↓ HTTP ↓
┌─────────────────────────────┬──────────────────┐
│  Data Layer: PostgreSQL      │  LLM: Qwen API   │
├─────────────────────────────┼──────────────────┤
│ • users                      │ • qwen-omni      │
│ • devices                    │   (语音转写)     │
│ • timeflow_templates         │ • qwen-plus      │
│ • focus_sessions             │   (学习总结)     │
│ • cards                       │ • 支持fallback   │
│ • review_schedules           │   (无额度使用)   │
│ • review_events              │                  │
│ • voice_drafts               │                  │
│ • ai_summaries               │                  │
└─────────────────────────────┴──────────────────┘
```

### 数据流示意

```
【专注计时流程】
手表开始专注 (TimeFlow模板) 
  ↓
每分钟更新计时时长至内存
  ↓
手表前台服务保障不被杀死
  ↓
用户完成 → 数据上报至后端
  ↓
CREATE FocusSession → 记入数据库
  ↓
手机端Dashboard自动刷新 → 显示今日总专注时长

【卡片复习流程】
后端定期查询 (select * from review_schedules where next_review_at <= now)
  ↓
手机/手表端 GET /reviews/due → 展示到期卡片列表
  ↓  
用户选择操作：
  ├─ "完成" → POST /reviews/events {action: "done"}
  │           ↓ Leitner算法计算 → new_box, next_review_at
  │           ↓ UPDATE review_schedule
  │
  └─ "稍后" → POST /reviews/events {action: "snooze", snooze_days: 2}
              ↓ next_review_at += 2 days
              ↓ UPDATE review_schedule

【语音建卡流程】
用户录音 (WAV格式, 16kHz单声道)
  ↓
POST /v1/voice/drafts (multipart/form-data)  ← 立即返回draft_id
  ↓
【后台异步处理】
  ├─ 调用Qwen-Omni-Flash转写语音
  ├─ 理解内容，提取关键信息
  ├─ 生成{front, back, tags}
  └─ 更新 voice_drafts.status = "done"
  ↓
【客户端轮询】
GET /v1/voice/drafts/{draft_id}
  ├─ status="processing" → 继续等待2s后再询问
  ├─ status="done" → 展示生成的卡片
  └─ status="failed" → 显示可编辑占位符
```

---

## 📦 项目结构

```
studyapp/code/
├── README.md                          # ← 本文件
├── client/
│   ├── kpforu_phone/                 # 手机端（Flutter）
│   │   ├── lib/src/
│   │   │   ├── app.dart              # 应用入口，Provider配置
│   │   │   ├── features/
│   │   │   │   ├── dashboard/        # 概览页（日/周报）
│   │   │   │   ├── timeflow/         # 时间流模板管理
│   │   │   │   ├── focus/            # 专注会话
│   │   │   │   ├── reviews/          # 复习卡片列表
│   │   │   │   ├── cards/            # 卡片编辑
│   │   │   │   ├── voice/            # 语音录制和上传
│   │   │   │   └── personalization/  # 个性化设置（壁纸/导出）
│   │   │   └── core/
│   │   │       ├── api_client.dart   # HTTP客户端（Base64+JWT）
│   │   │       ├── ai_wait_policy.dart # 统一超时参数
│   │   │       ├── session_state.dart  # 用户鉴权状态
│   │   │       └── wallpaper_store.dart # 壁纸管理
│   │   └── pubspec.yaml
│   │
│   └── kpforu_watch/                 # 手表端（Flutter）
│       ├── lib/src/
│       │   ├── app.dart              # 圆屏适配入口
│       │   ├── features/
│       │   │   ├── focus/            # 专注计时（圆屏全屏）
│       │   │   ├── focus_timer/      # 前台服务+振动
│       │   │   ├── reviews/          # 待办卡片（轻量展示）
│       │   │   ├── voice/            # 语音采集
│       │   │   ├── binding/          # 设备绑定
│       │   │   └── watch_settings/   # 设置页
│       │   └── core/
│       │       ├── api_client.dart
│       │       └── foreground_service.dart # 前台服务
│       └── pubspec.yaml
│
├── server/                            # FastAPI后端
│   ├── app/
│   │   ├── main.py                   # FastAPI应用启动
│   │   ├── api/                      # 路由层
│   │   │   ├── __init__.py           # 路由聚合
│   │   │   ├── auth.py               # JWT鉴权
│   │   │   ├── binding.py            # 设备绑定
│   │   │   ├── timeflow.py           # 模板管理
│   │   │   ├── focus.py              # 专注会话
│   │   │   ├── reviews.py            # 复习事件
│   │   │   ├── cards.py              # 卡片CRUD
│   │   │   ├── voice.py              # 语音上传/处理
│   │   │   └── ai.py                 # 总结和导出
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── leitner.py            # Leitner算法实现
│   │   │   ├── qwen_client.py        # Qwen API调用
│   │   │   ├── ai_summary.py         # 总结生成（含缓存）
│   │   │   ├── pdf_export.py         # PDF导出模板
│   │   │   └── ...
│   │   ├── models/                   # SQLAlchemy数据模型
│   │   │   ├── user.py
│   │   │   ├── device.py
│   │   │   ├── timeflow.py
│   │   │   ├── focus.py
│   │   │   ├── card.py
│   │   │   ├── review.py
│   │   │   └── voice.py
│   │   ├── schemas/                  # Pydantic数据验证
│   │   ├── core/                     # 配置和依赖注入
│   │   │   ├── config.py             # 环境变量配置
│   │   │   ├── auth.py               # JWT逻辑
│   │   │   └── dependencies.py       # 依赖注入
│   │   └── db/
│   │       └── session.py            # 数据库连接
│   ├── alembic/                      # 数据库迁移
│   ├── tests/                        # 单元测试
│   ├── scripts/
│   │   └── start_backend.ps1         # Windows启动脚本
│   ├── requirements.txt              # Python依赖
│   ├── Dockerfile                    # Docker镜像定义
│   ├── docker-compose.yml            # 本地开发环境
│   └── README.md
│
└── docs/                             # 文档和记录
    ├── tech_overview.md              # 技术概览
    ├── video_script_phone.md         # 手机端功能演示稿
    ├── video_script_watch.md         # 手表端功能演示稿
    └── video_script_dual.md          # 双端协同演示稿 ← 本视频使用
```

---

## 🚀 快速开始

### 环境要求
- **Windows 10/11** （开发演示环境）
- **Flutter 3.10+** （双端编译）
- **Python 3.9+** （后端运行）
- **PostgreSQL 13+** 或 SQLite（本地开发）
- **通义千问API Key** （首次注册免费额度）

### 第1步：克隆并准备环境

```bash
# 1. 克隆项目
git clone <repo-url> studyapp
cd studyapp/code

# 2. 配置环境变量 (.env 放在 server 目录)
cat > server/.env << EOF
DATABASE_URL=sqlite:///./runtime.db  # 或 postgresql://user:pass@localhost/kpforu
JWT_SECRET_KEY=your-secret-key-min-32-chars
DASHSCOPE_API_KEY=sk-xxx...          # 申请地址: https://dashscope.aliyun.com
QWEN_TEXT_MODEL=qwen-plus
QWEN_VOICE_MODEL=qwen-omni-flash
EOF
```

### 第2步：启动后端（API服务）

#### 方式A：使用 Docker Compose (推荐，一键启动)
```bash
cd server
docker-compose up --build
# 稍等2-3分钟后，访问 http://127.0.0.1:8000/docs 查看API文档
```

#### 方式B：本地Python运行
```bash
cd server
conda create -n kpforu-server python=3.9
conda activate kpforu-server
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 第3步：启动手机端

```bash
cd client/kpforu_phone
flutter pub get
flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1
# 稍等1-2分钟后，Windows应用窗口自动启动
```

### 第4步：启动手表端

```bash
cd client/kpforu_watch
flutter pub get
flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1
# 手表模拟器窗口启动（可调整窗口大小对应不同屏幕尺寸）
```

### 第5步：首次绑定设备

1. 手机端 → **个性化** → **设备管理** → **与手表配对**
2. 输入配对码（6位数字，手表端显示）
3. 完成后自动跳转登录，建议使用测试账号
4. 两端都成功进入Dashboard，完成！

---

## 🎬 功能演示（完整流程）

### 场景A：创建专注模板并执行

**时间**：2分钟

```
【界面1】 手机 → Dashboard
  看到今天还没有专注任务

【界面2】 手机 → TimeFlow (时间流)
  按钮：+ 新建模板
  输入：
    模板名称: "英语单词复习30分"
    - 段1: 预热, 2分钟
    - 段2: 主学, 20分钟  
    - 段3: 复习, 5分钟
    - 段4: 反思, 3分钟
  点击：保存

【界面3】 手机 → Dashboard → 立即开始
  跳转到手表界面

【界面4】 手表 → 全屏倒计时 (Segment 1: 预热)
  显示大字数字倒计时
  按钮：暂停、结束   
  (时间到自动跳下一段，同时振动+语音通知)

【界面5】 手表 → 依次切换段落 (段2→段3→段4)
  用户全程参与 2 分钟快速演示

【界面6】 手表 → 结束确认弹层
  "已完成本轮34分钟的英语复习，数据已同步"

【验证】 手机 → Dashboard 
  看到今日专注时长: 34分钟 ↑
  专注科目: 英语 × 1 ↑
```

---

### 场景B：语音快速建卡

**时间**：2分钟

```
【界面1】 手机 → 个性化 → 语音建卡
  按钮：开始录音（红色按钮）

【界面2】 用户边走边说：
  "日本战国时期的织田信长有什么历史成就？他通过什么手段统一了日本？"
  (共录制45秒)

【界面3】 点击停止录音
  自动上传到后端
  UI显示: "正在处理音频..."

【后台处理】 (~5-10秒)
  ├─ Qwen语音识别转写
  ├─ 理解内容，提取问答对
  └─ 生成卡片草稿

【界面4】 手机自动弹出生成的卡片：
  前面: "日本战国时期织田信长有什么历史成就？"
  背面: "织田信长（1534-1582）是日本战国时期的军事统帅，
        主要成就包括：
        1. 打破梯田制，集中中央权力
        2. 改革行政制度，设置常设公务员
        3. 推进大名割据的统一进程
        4. 建立安土城堡作为行政中心
        5. 支持传教士，开放对外贸易"
  标签: #日本历史 #织田信长 #战国时期

【用户操作】 点击"确认"按钮
  卡片立即进入复习系统，box=1, next_review_at = 明天

【验证】 手机 → 复习待办
  看到"织田信长的历史成就"卡片已在待办列表
  (同时手表端也自动同步了这张卡)
```

---

### 场景C：间隔复习完整流程

**时间**：3分钟

```
【前提条件】 系统中已有5张复习卡片

【界面1】 手机 → 复习 (Reviews)
  显示5张到期卡片，按优先级排序

【界面2】 点击第1张卡片
  前面: "Python中什么是装饰器？"
  用户阅读答案，理解了
  点击: "完成" ✓

【后台处理】
  原来: Box 1 (1天间隔)
  现在: Box 2 (2天间隔)  
  下次复习: 2026-03-29

【界面3】 用户继续，第2张卡片
  前面: "什么是HTTP请求头？"
  用户看了下，不太确定
  点击: "稍后" (延期1天)

【后台处理】
  Box 1 (保持不变)
  extends next_review_at += 1 天
  下次复习: 2026-03-28

【界面4】 第3张卡片
  用户点击: "删除" 按钮
  确认弹层: "确认删除此卡片？"
  点击: "确认删除"
  卡片从系统移除（不计入复习统计）

【验证】 
  完成了3张卡；
  下拉刷新，列表自动更新
  手表端复习待办也自动更新
```

---

### 场景D：AI学习总结与PDF导出

**时间**：4分钟

```
【界面1】 手机 → Dashboard (概览)
  显示：
    📊 今日专注: 165分钟
       ├─ 地理: 60分钟
       ├─ 英语: 55分钟
       └─ 编程: 50分钟
    📚 复习进度: 45张完成, 8张延期
    
【界面2】 点击"日报详情"或"周报详情"
  后端自动调用Qwen生成分析报告（首次生成，~3-5秒）

【界面3】 显示日报详情：
  ┌─────────────────────────────────────┐
  │  2026-03-27 学习总结               │
  ├─────────────────────────────────────┤
  │ 📊 学习时长                         │
  │   今日: 165分钟  周均: 142分钟      │
  │   比昨日: ↑ 20分钟 (13%)            │
  │                                     │
  │ 🔄 复习成效                         │
  │   完成: 45张  延期: 8张             │
  │   升盒率: 85% (较高效率)            │
  │                                     │
  │ 💡 AI建议                          │
  │   您的学习强度稳定，建议继续       │
  │   保持当前节奏。地理科目最近调   │
  │   高了学习时间投入，效果显著。   │
  │   再加强一下编程的复习频次。      │
  │                                     │
  │ 📅 本周趋势 (折线图省略)            │
  └─────────────────────────────────────┘

【界面4】 点击"导出PDF"
  系统后台生成PDF（包含图表+数据表）
  下载到手机本地 (~10秒)
  自动打开预览

【界面5】 PDF预览
  包含内容：
    - 标题: "2026年3月 学习总结"
    - 学习时长柱状图 (每天)
    - 掌握度折线图 (各科目)
    - 复习箱体分布 (Box1-5)
    - 详细数据表格
    - AI智能建议段落

【用户操作】 
  可分享PDF给朋友/家长
  或导入到学习日志
```

---

### 场景E：手表端离线操作与数据同步

**时间**：2分钟（模拟网络切断）

```
【前提】 手表已绑定手机，建立了数据连接

【界面1】 模拟断网（拔掉网线 或 关闭WiFi）
  
【界面2】 手表 → 复习待办
  虽然离线，但本地缓存的卡片仍可显示
  用户点击"完成"按钮

【后台】 (离线模式)
  操作记录存储在本地 SharedPreferences
  {action: "done", card_id: "xxx", timestamp: "..."}

【界面3】 恢复网络连接
  手表自动检测网络（每5秒check一次）
  自动同步离线操作到云端

【后台】 (云端同步)
  POST /v1/reviews/events {action: "done", ...}
  ├─ 服务器确认收到
  ├─ 更新数据库 review_schedule
  ├─ 响应200 OK
  └─ 本地缓存清空

【验证】 手机 → Dashboard 
  手表的离线操作数据已同步上来
  今日完成数 +1
```

---

## 🔧 配置与定制

### 修改Leitner间隔（自定义复习周期）

编辑文件：`server/app/core/config.py`

```python
LEITNER_INTERVALS = {
    1: 1,      # Box 1: 1天后
    2: 3,      # Box 2: 3天后 (改成3)
    3: 7,      # Box 3: 7天后
    4: 14,     # Box 4: 14天后
    5: 30      # Box 5: 30天后 (改成30)
}
```

### 修改AI模型（更换或降本）

编辑文件：`server/.env`

```bash
# 使用成本更低的Qwen3基础版
QWEN_VOICE_MODEL=qwen3-turbo          # 语音转写（成本更低）
QWEN_TEXT_MODEL=qwen-turbo            # 学习总结（成本更低）

# 或使用完全离线模式（fallback Chinese仅供演示）
ENABLE_LLM_CALLS=false                # 禁用所有LLM调用
```

### 调整超时参数（网络较慢时）

编辑文件：`client/kpforu_phone/lib/src/core/ai_wait_policy.dart`

```dart
class AiWaitPolicy {
  static const int requestTimeout = 120;    // 上传超时改成120秒
  static const int pollTimeout = 180;       // 总等待改成180秒
  static const int exportRequestTimeout = 240; // 导出改成240秒
}
```

---

## 📊 质量保证

### 代码质量检查

```bash
# 手机端
cd client/kpforu_phone
flutter analyze                # ✅ No issues found!

# 手表端  
cd client/kpforu_watch
flutter analyze                # ✅ 通过关键模块检查

# 后端
cd server
pytest tests/                  # ✅ 所有用例通过
```

### 功能验证清单

- ✅ 时间流模板：创建/编辑/删除/执行
- ✅ 专注计时：手表前台服务保障，不被系统杀死
- ✅ 语音建卡：上传→转写→自动生成卡片
- ✅ 间隔复习：Leitner算法自动调度
- ✅ AI总结：日/周报自动生成（含缓存策略）
- ✅ PDF导出：支持图表和详细数据
- ✅ 双端同步：实时数据一致性
- ✅ 离线操作：手表本地缓存，恢复网络后自动同步
- ✅ 圆屏适配：手表安全区布局正确

---

## 🐛 常见问题

### Q1: 语音建卡总是失败（status="failed"）
**A:** 
1. 检查后端日志：`docker-compose logs api | grep voice`
2. 确认API额度：登录 https://dashscope.aliyun.com 查看可用模型
3. 若显示"403 Forbidden"→ API额度已用尽，需充值
4. 临时方案：编辑 `.env` 将 `ENABLE_LLM_CALLS=false`，系统会返回fallback中文模板

### Q2: 手表无法接收到复习卡片更新
**A:**
1. 确认手机和手表已成功配对（个性化→设备管理）
2. 检查两端网络连接（建议关闭VPN）
3. 手动刷新手表 → 复习待办（下拉刷新）
4. 查看手表日志：`adb logcat | grep kpforu`

### Q3: 后端启动报错 `ModuleNotFoundError: No module named 'app'`
**A:** 
1. 确保当前目录是 `server/` 
2. 运行：`pip install -e .` 或 `export PYTHONPATH=$PWD`
3. 确认Python版本≥3.9：`python --version`

### Q4: 手机端无法连接到后端（ConnectionRefused）
**A:**
1. 检查后端是否真的在运行：`curl http://127.0.0.1:8000/docs`
2. 确认 `BASE_URL` 参数正确：`--dart-define=BASE_URL=http://127.0.0.1:8000/v1`
3. 若使用实机测试，需改成内网IP而非127.0.0.1

### Q5: PDF导出时间太长（>30秒）
**A:**
1. 数据量过大，Qwen处理时间较长，属于正常（首次生成）
2. 第二次导出同一天数据会走缓存，快速返回（<2秒）
3. 若要加快，可减少导出周期（只导出1周而不是1个月）

---

## 🔐 安全提示

### 生产部署前必读

1. **环境变量保护**
   ```bash
   # ❌ 错误：密钥明文存储
   DASHSCOPE_API_KEY=sk-xxx  # 不要提交到Git!
   
   # ✅ 正确：使用密钥管理服务
   # AWS Secrets Manager / 阿里云密钥中心 / HashiCorp Vault
   ```

2. **JWT密钥强度**
   ```bash
   # 生成强密钥（32字符以上）
   openssl rand -hex 32
   # 输出: a3f7c2e1b9d4f8a6c2e1b9d4f8a6c2e1b9d4f8a
   ```

3. **数据库连接**
   ```bash
   # 禁用SQLite，生产使用PostgreSQL
   DATABASE_URL=postgresql://user:secure-password@prod-db.com:5432/kpforu
   # 启用SSL/TLS连接
   DATABASE_URL=postgresql://...?sslmode=require
   ```

4. **API限流**
   ```python
   # server/app/core/middleware.py
   # 部署时添加请求速率限制，防止滥用
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

---

## 📚 参考文档

- 📖 **后端详细说明** → [server/README.md](server/README.md)
- 📱 **手机端说明** → [client/kpforu_phone/README.md](client/kpforu_phone/README.md)
- ⌚ **手表端说明** → [client/kpforu_watch/README.zh-CN.md](client/kpforu_watch/README.zh-CN.md)
- 🔧 **技术深度解析** → [docs/tech_overview.md](docs/tech_overview.md)
- 🎬 **视频演示稿** → [docs/video_script_dual.md](docs/video_script_dual.md)

---

## 🎓 关于Leitner算法

Leitner间隔复习系统是基于"遗忘曲线"（Forgetting Curve）理论的学习方法。当我们学习新知识时，如果不进行复习，遗忘速度很快。但如果在关键时点（即将忘记时）进行复习，可以大幅延长记忆周期。

```
遗忘曲线示意：
记忆强度
    ↑
  100│╲
    │ ╲___
   80│     ╲___
    │         ╲__
   60│            ╲__
    │               ╲___
   40│─────────────────╲___  ← 无复习
    │
   20│
    │
    0└─────────────────────→ 天数
      
复习效果：
记忆强度      
    ↑
  100│╲___     ╲___     ╲___     ╲___
    │     ╲___     ╲___     ╲___     → 长期记忆
   80│
    │
   60│
    │
   40│    ↑       ↑       ↑       ↑
    │  1天     2天     4天     7天     (复习间隔)
    │
    0└──────────────────────────────→ 天数
```

KpForU 的 Leitner 盒子模型：
- **Box 1** (新卡片) → 1天后复习
- **Box 2** → 2天后复习  
- **Box 3** → 4天后复习
- **Box 4** → 7天后复习
- **Box 5** (已掌握) → 14天后复习（可选）

每当用户答对时，卡片升一个盒子；答错时，重置到 Box 1 重新开始。这样确保学生在最佳遗忘点进行复习，达到事半功倍的学习效率。

---

## 📞 支持与反馈

遇到问题或有功能建议？

1. 📝 提交Issue：GitHub Issues
2. 💬 讨论功能：GitHub Discussions  
3. 📧 邮件反馈：2934487705@qq.com

---

## 📄 许可证

本项目采用 MIT License。详见 [LICENSE](LICENSE)

---

**KpForU** — *让学习变得更高效，让目标触手可及* 🚀
