# 数据库问题修复说明

## 问题诊断

### 症状
1. **找到5个工作但0个保存到数据库**
2. **错误信息**: `column jobs.selected_template does not exist`

### 根本原因
Neon PostgreSQL 数据库中的 `jobs` 表结构**过期**，缺少新增的列：
- `selected_template` - Resume Export功能需要的列

代码模型（`modules/database.py`）已经定义了这些列，但数据库表还没有更新。

---

## ✅ 已完成的修复

已经运行了数据库迁移脚本，添加了缺失的列：

```bash
python scripts\quick_fix_database.py
```

**执行结果**: ✅ SUCCESS - Column 'selected_template' added to jobs table

---

## 🔍 问题详解

### 为什么会出现这个问题？

1. **SQLAlchemy ORM** 定义了完整的表结构（包括 `selected_template`）
2. 但 **Neon 数据库中的实际表** 还是旧的结构
3. 当 `get_recent_jobs()` 查询数据库时，SQLAlchemy 尝试查询所有已定义的列
4. PostgreSQL 发现 `selected_template` 列不存在，抛出错误

### SQL查询错误示例：
```sql
SELECT jobs.id, jobs.title, jobs.selected_template, ...  -- ❌ selected_template不存在
FROM jobs
WHERE ...
```

---

## 📁 创建的修复文件

### 1. `migrations/add_missing_columns.sql`
手动SQL迁移脚本（如果你想在Neon控制台手动运行）

### 2. `scripts/migrate_database.py`
完整的Python迁移脚本（带验证和错误处理）

### 3. `scripts/quick_fix_database.py` ⭐
**快速修复脚本**（已成功执行）

### 4. `scripts/test_database.py`
数据库结构测试脚本

---

## 🚀 验证修复

运行以下命令验证数据库已修复：

```bash
python scripts\test_database.py
```

应该看到：
```
✅ Database is ready to use!
```

---

## 💡 如何测试Job Search功能

1. **重启Streamlit应用** (如果正在运行)：
   - 停止当前运行: `Ctrl+C`
   - 重新启动: `streamlit run streamlit_app.py`

2. **在UI中测试**：
   - 点击 "🔍 Search Jobs" 按钮
   - 应该看到 "Found and scored 5 jobs! (5 saved to database)" ✅
   - 点击 "📦 Load Cached Jobs" 按钮
   - 应该能成功加载数据库中的工作 ✅

---

## 🔧 未来如何避免此类问题？

### 方案1: 使用Alembic进行数据库版本管理
```bash
# 安装alembic
pip install alembic

# 初始化（已有alembic文件夹，跳过）
# alembic init alembic

# 创建新迁移
alembic revision --autogenerate -m "Add resume export columns"

# 运行迁移
alembic upgrade head
```

### 方案2: 在应用启动时自动同步表结构
在 `modules/database.py` 中添加：
```python
# 开发模式下自动创建/更新表
if os.getenv("DEV_MODE") == "true":
    Base.metadata.create_all(bind=engine)
```

⚠️ **注意**: 生产环境不要使用 `create_all()`，应该使用Alembic迁移

---

## 📊 当前数据库状态

### 连接信息
- **类型**: PostgreSQL (Neon)
- **状态**: ✅ 已连接
- **表结构**: ✅ 已更新

### Jobs表现有列（更新后）
- ✅ `id`, `title`, `company`, `description`
- ✅ `location`, `salary`, `is_remote`
- ✅ `posted_date`, `expiration_date`, `job_age`
- ✅ `job_url`, `apply_url`, `company_url`
- ✅ `job_type`, `occupation`, `benefits`, `rating`
- ✅ `match_score`, `match_reasoning`, `ats_score`
- ✅ `job_category`, `scraped_source`
- ✅ `selected_template` ⭐ **新增**
- ✅ `created_at`

---

## ❓ 常见问题

### Q: 为什么Search Jobs时显示"0 saved to database"？
A: 很可能之前搜索的工作已经存在于数据库中（根据`job_url`去重）。删除旧数据或搜索不同的关键词。

### Q: 如何清空数据库重新测试？
A: 在Neon控制台运行：
```sql
TRUNCATE TABLE jobs CASCADE;
```

### Q: 如何查看数据库中有多少工作？
A: 运行：
```python
python -c "from modules.database import SessionLocal, Job; db = SessionLocal(); print(f'Total jobs: {db.query(Job).count()}'); db.close()"
```

---

## 📞 相关文件位置

- 数据库模型: `modules/database.py`
- 工作爬虫: `modules/job_scraper.py`
- Streamlit UI: `streamlit_app.py`
- 迁移脚本: `scripts/quick_fix_database.py`
- 测试脚本: `scripts/test_database.py`

---

**修复完成时间**: 2026-01-13  
**修复状态**: ✅ 成功
