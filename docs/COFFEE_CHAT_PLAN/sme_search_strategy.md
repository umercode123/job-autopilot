# 域名驱动的 LinkedIn 搜索策略

## 🚨 核心问题

加拿大大部分公司是中小企业，很多：
- ❌ 没有LinkedIn Company Page
- ❌ 或者名字不一样（Job posting vs LinkedIn）  
- ❌ 用 `Current Company` filter 找不到人

## ✅ 解决方案：**域名是唯一标准**

你说得对！公司名会变化，但**域名不会**：
- Job posting: "ABC Learning Inc"
- LinkedIn: "ABC Learning Solutions"  
- **域名都是**: `abclearning.com` ✅

而且你的 `Job` 数据库已经有 `company_domain` 字段了！

---

## 🔑 Step 1: 用域名找LinkedIn Company

```python
def find_linkedin_company_by_domain(domain):
    """
    用域名找LinkedIn company page
    
    Args:
        domain: e.g., "shopify.com"
        
    Returns:
        LinkedIn company URL or None
    """
    # LinkedIn搜索：用域名作为关键词
    search_url = f'https://www.linkedin.com/search/results/companies/?keywords={domain}'
    
    # LinkedIn会自动识别域名对应的公司
    # Example: shopify.com → Shopify Inc. (LinkedIn Company)
    
    companies = linkedin_search(search_url)
    
    if companies and len(companies) > 0:
        # 取第一个结果（通常是准确的）
        return companies[0]['linkedin_company_url']
    
    return None
```

---

## 🔍 Step 2: 用Company Page搜索校友

```python
def search_alumni_by_domain(domain, schools):
    """
    基于域名搜索校友
    
    Args:
        domain: 公司域名 (e.g., "shopify.com")
        schools: 学校列表 (e.g., ["University of Western Ontario", "York University"])
        
    Returns:
        List of alumni contacts
    """
    # Step 1: 找LinkedIn company page
    company_page = find_linkedin_company_by_domain(domain)
    
    all_alumni = []
    
    for school in schools:
        if company_page:
            # Step 2a: 用company page ID搜索（精确）
            company_id = extract_company_id(company_page)
            search_url = f'https://www.linkedin.com/search/results/people/?currentCompany=["{company_id}"]&school=["{school}"]'
            
            results = linkedin_search(search_url)
            
            if results:
                print(f"✅ Found {len(results)} {school} alumni at {domain}")
                for r in results:
                    r.domain_verified = True  # 高置信度
                    r.search_method = "precise"
                all_alumni.extend(results)
        else:
            # Step 2b: Fallback - 用域名作为keyword
            print(f"⚠️ No LinkedIn page for {domain}, using keyword search")
            
            # 去掉 .com/.ca 等后缀，提高匹配率
            domain_base = domain.replace('.com', '').replace('.ca', '').replace('.io', '')
            
            search_url = f'https://www.linkedin.com/search/results/people/?keywords="{domain_base}" "{school}"'
            
            results = linkedin_search(search_url)
            
            # 验证结果：检查profile里是否真的提到这个域名
            verified = []
            for person in results:
                # 检查当前公司是否匹配域名base
                if domain_base.lower() in person.current_company.lower():
                    person.domain_verified = True
                    person.search_method = "keyword_verified"
                    verified.append(person)
            
            if verified:
                print(f"✅ Found {len(verified)} {school} alumni (keyword verified)")
                all_alumni.extend(verified)
    
    return all_alumni
```

---

## 📊 Example Flow

### Case 1: 大公司 (有LinkedIn page)

```
Job:
  company: "Shopify"
  domain: "shopify.com"
  match_score: 8

Step 1: Search LinkedIn companies for "shopify.com"
  → Found: linkedin.com/company/shopify

Step 2: Search alumni at Shopify company page
  → UWO: Found 5 alumni
  → York: Found 2 alumni

Result: ✅ 7 contacts (domain_verified=True)
```

### Case 2: 中小企业 (有domain但没LinkedIn page)

```
Job:
  company: "ABC Learning Inc"
  domain: "abclearning.com"
  match_score: 7

Step 1: Search LinkedIn for "abclearning.com"
  → Not found (no company page)

Step 2: Keyword search "abclearning" + "UWO"
  → Found 2 people
  
Step 3: Verify by domain base
  - Person A: Works at "ABC Learning Solutions" ✅ (matches "abclearning")
  - Person B: Mentions "ABC Corp" ❌ (doesn't match)

Result: ✅ 1 contact (domain_verified=True via keyword)
```

### Case 3: 中小企业 (没有domain)

```
Job:
  company: "Small Local Startup"
  domain: None  (Job scraper couldn't extract)
  match_score: 9

Fallback: Use company name
  → Search "Small Local Startup" + "UWO"
  → Found 1 person
  → domain_verified = False (低置信度)

Result: ⚠️ 1 contact (需要手动验证)
```

---

## 🎯 优先级评分（平等对待所有公司）

```python
def calculate_priority(contact):
    """
    All companies treated equally
    大厂和中小企业平等对待
    """
    score = 0
    
    # Factor 1: Job match score (0-10 → 0-40)
    if contact.job_match_score:
        score += contact.job_match_score * 4
    
    # Factor 2: 校友 (+30)
    if contact.is_alumni:
        score += 30
    
    # Factor 3: Connection degree
    if contact.connection_degree == '2nd':
        score += 20
    elif contact.connection_degree == '3rd':
        score += 10
    
    # Factor 4: Domain match confidence
    if contact.domain_verified:  # 域名验证通过
        score += 10  # 高置信度
    else:
        score += 0   # 名字匹配（低置信度）
    
    return score
```

**不区分公司大小！所有公司平等！**

Priority Tiers:
```
90-100: 🔥 高分job + 校友 + 2nd degree + domain verified
70-89:  ⭐ 好job + 校友 + domain verified  
50-69:  📌 校友 OR 好job
<50:    ⬇️ Skip
```

---

## 🛡️ Domain Extraction (已有)

你的 `job_scraper.py` 已经有了：

```python
JobScraper.extract_company_domain(url)
# Example:
# Input: "https://careers.shopify.com/jobs/123"
# Output: "shopify.com"
```

所以domain已经存在数据库了！✅

---

## 📦 Database Integration

```python
def daily_coffee_chat_workflow():
    """
    基于域名的每日workflow
    """
    # Step 1: 获取高分jobs（有domain的优先）
    jobs_with_domain = session.query(Job).filter(
        Job.match_score >= 7,
        Job.company_domain.isnot(None)
    ).order_by(Job.match_score.desc()).all()
    
    jobs_without_domain = session.query(Job).filter(
        Job.match_score >= 7,
        Job.company_domain.is_(None)
    ).order_by(Job.match_score.desc()).all()
    
    print(f"📥 Jobs with domain: {len(jobs_with_domain)}")
    print(f"📥 Jobs without domain: {len(jobs_without_domain)}")
    
    # Step 2: 优先处理有domain的jobs
    all_contacts = []
    
    # 按domain去重（避免重复搜索同一公司）
    domains_processed = set()
    
    for job in jobs_with_domain:
        domain = job.company_domain
        
        if domain in domains_processed:
            continue  # 已经搜索过这个公司了
        
        domains_processed.add(domain)
        
        print(f"\n🔍 Searching {domain}...")
        
        # 搜索校友
        alumni = search_alumni_by_domain(domain, user_profile.schools)
        
        # 链接job信息
        for contact in alumni:
            contact.related_job_id = job.id
            contact.job_match_score = job.match_score
            contact.company_domain = domain
        
        all_contacts.extend(alumni)
    
    # Step 3: 处理没domain的jobs（低优先级）
    for job in jobs_without_domain[:5]:  # 限制5个，避免太多不准确结果
        print(f"\n⚠️ Searching {job.company} (no domain)...")
        
        # 用公司名搜索（低置信度）
        alumni = search_alumni_by_name(job.company, user_profile.schools)
        
        for contact in alumni:
            contact.related_job_id = job.id
            contact.job_match_score = job.match_score
            contact.domain_verified = False  # 标记为未验证
        
        all_contacts.extend(alumni)
    
    # Step 4: 计算优先级并保存
    for contact in all_contacts:
        contact.priority_score = calculate_priority(contact)
    
    all_contacts.sort(key=lambda c: c.priority_score, reverse=True)
    
    # 保存到数据库...
    
    return all_contacts
```

---

## 📊 Dashboard Display

```
┌────────────────────────────────────────────┐
│ Today's Contacts (25)                      │
├────────────────────────────────────────────┤
│ 🔥 HIGH Priority (8 people)                │
│   • Sarah @ shopify.com (Score: 95)        │
│     [Domain ✓] [2nd] [UWO] [Job: 8/10]    │
│                                             │
│   • John @ amazon.com (Score: 92)          │
│     [Domain ✓] [2nd] [UWO] [Job: 9/10]    │
│   ...                                       │
│                                             │
│ ⭐ MEDIUM Priority (12 people)             │
│   • Lisa @ td.com (Score: 85)              │
│     [Domain ✓] [3rd] [York] [Job: 7/10]   │
│   ...                                       │
│                                             │
│ ⬇️ LOW Priority - Verify (5 people)        │
│   • Mike @ Small Startup (Score: 55)       │
│     [Domain ✗] [2nd] [UWO] [Job: 9/10]    │
│     ⚠️ Manual verification needed          │
│   ...                                       │
└────────────────────────────────────────────┘
```

---

## ✅ Summary

**修正后的策略：**

1. ✅ **域名是唯一标准** - `company_domain` 字段
2. ✅ **大厂+中小企业平等** - 不区分优先级
3. ✅ **Domain verification** - 高置信度标记
4. ✅ **使用现有数据** - Job table已有domain

**搜索流程：**
```
有Domain → 找LinkedIn company page → 搜索校友 (高置信度)
无Domain → 用公司名keyword搜索 → 手动验证 (低置信度)
```

**优先级：**
- Job分数 × 4  
- 校友 +30  
- 2nd degree +20  
- Domain verified +10  
→ 总分0-100，不区分公司大小！

这样对吗？
