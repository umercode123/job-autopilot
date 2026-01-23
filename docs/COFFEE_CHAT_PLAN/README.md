# Coffee Chat Plan

## 📋 核心文档

| 文件 | 说明 |
|------|------|
| [IMPLEMENTATION_PLAN_v6.md](./IMPLEMENTATION_PLAN_v6.md) | **主要实施计划** - 包含所有Phase详情 |
| [MCP_ARCHITECTURE.md](./MCP_ARCHITECTURE.md) | Chrome DevTools MCP架构说明 |

---

## 🎯 Phase概览

| Phase | 内容 | 时间 | 状态 |
|-------|------|------|------|
| 0 | 安全检查（登录、周末、验证码） | 30分钟 | ✅ 完成 |
| 1 | 工作流修复（公司验证、多学校） | 1-2小时 | ✅ 完成 |
| 2 | AI Agents实现 + 数据验证 | 1-2小时 | ✅ 完成 |
| 3 | Memory Layer（ChromaDB） | 1-2小时 | ✅ 完成 |
| 4 | Hidden Job信号检测 | 1小时 | ✅ 完成 |
| 5 | 每日状态检查 | 1小时 | ✅ 完成 |
| 6 | 消息功能 + Profile读取 | TBD | ⏳ 待开始 |

---

## 🔧 LLM配置

| 用途 | 推荐 |
|------|------|
| 简历优化 | GPT-4o |
| 消息/润色 | Gemini 2.5 Flash |
| 分析/打分 | GPT-4o-mini |

---

## ✅ 已确认决定

- 周末不发送
- Email通知验证码
- AI决定是否发note（每天5个限额）
- Chrome自动导入connections
- 每天检查一次状态
- AI披露必须加在消息末尾

---

## 📁 相关文件

```
modules/
├── agent_manager.py           # ✅ Agent编排器（新）- 完整Pipeline
├── coffee_chat_agents.py      # ✅ AI Agents（已增强 - 添加generate_message）
├── coffee_chat_memory.py      # ✅ ChromaDB Memory Layer（已增强）
├── coffee_chat_models.py      # Database Models
├── linkedin_automation.py     # LinkedIn搜索
├── llm_config.py              # ✅ LLM配置（新）- Gemini/OpenAI
├── rate_limiter.py            # ✅ 每日限流控制（新）
├── checkpoint.py              # ✅ 中断恢复（新）
├── gmail_service.py           # ✅ Gmail服务（已增强 - 添加通知）
├── hidden_job_detector.py     # ✅ Hidden Job检测（新）
└── data_validator.py          # ✅ 数据验证（新）

scripts/
├── linkedin_auto_connect.py   # ✅ 主自动化脚本（v2 - 已重写）
├── daily_check.py             # ✅ 每日状态检查（新）
└── import_connections.py      # ✅ 导入现有connections（新）

pages/
├── coffee_chat_center.py      # Coffee Chat UI
└── user_profile.py            # 用户配置
```

---

## 🚀 使用方法

### 1. 主自动化脚本
```bash
# 基本用法
python scripts/linkedin_auto_connect.py --company "shopify" --school "University of Western Ontario" --limit 5

# 多学校搜索
python scripts/linkedin_auto_connect.py --company "google" --school "UWO" "Waterloo" --limit 10

# 不带note
python scripts/linkedin_auto_connect.py --company "meta" --school "Western" --no-note
```

### 2. 每日检查
```bash
# 检查连接状态
python scripts/daily_check.py

# 只看本地统计（不开浏览器）
python scripts/daily_check.py --skip-browser
```

### 3. 导入现有连接
```bash
# 导入现有connections到Memory
python scripts/import_connections.py --pages 5
```

---

## ⚠️ 需要配置

在 `.env` 文件中添加：
```
GOOGLE_API_KEY=你的Gemini_API密钥
```
获取地址: https://makersuite.google.com/app/apikey

---

*更新日期: 2026-01-22*
