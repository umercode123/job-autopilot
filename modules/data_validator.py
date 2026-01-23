"""
Data Validator for LinkedIn Automation
验证AI提取的数据是否正确，防止人名/公司名搞混
"""
import os
import re
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logger_config import app_logger

# 公司名称常见后缀
COMPANY_INDICATORS = [
    'Inc', 'Inc.', 'LLC', 'Ltd', 'Ltd.', 'Corp', 'Corp.', 'Corporation',
    'Company', 'Co.', 'Co', 'Technologies', 'Tech', 'Solutions', 'Services',
    'Group', 'Holdings', 'Partners', 'Consulting', 'Global', 'International',
    'Labs', 'Studio', 'Studios', 'Media', 'Digital', 'Software', 'Systems',
    'Industries', 'Ventures', 'Capital', 'Financial', 'Bank', 'Insurance'
]

# 常见人名模式（用于检测）
PERSON_NAME_PATTERNS = [
    r'^[A-Z][a-z]+ [A-Z][a-z]+$',  # "John Smith"
    r'^[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+$',  # "John A. Smith"
    r'^[A-Z][a-z]+ [A-Z][a-z]+-[A-Z][a-z]+$',  # "Mary Smith-Jones"
]


def looks_like_company_name(name: str) -> bool:
    """
    检查名称是否看起来像公司名
    
    Args:
        name: 要检查的名称
        
    Returns:
        True if looks like a company name
    """
    if not name:
        return False
    
    name_upper = name.strip()
    
    # 检查公司后缀
    for indicator in COMPANY_INDICATORS:
        if name_upper.endswith(indicator) or f' {indicator}' in name_upper:
            return True
    
    # 全大写或包含大量大写字母可能是公司名
    if name_upper.isupper() and len(name_upper) > 3:
        return True
    
    # 包含特殊字符如 & 或 @ 可能是公司名
    if '&' in name_upper or '@' in name_upper:
        return True
    
    return False


def looks_like_person_name(name: str) -> bool:
    """
    检查名称是否看起来像人名
    
    Args:
        name: 要检查的名称
        
    Returns:
        True if looks like a person name
    """
    if not name:
        return False
    
    name = name.strip()
    
    # 检查常见人名模式
    for pattern in PERSON_NAME_PATTERNS:
        if re.match(pattern, name):
            return True
    
    # 只有2-3个单词，每个以大写开头
    words = name.split()
    if 2 <= len(words) <= 3:
        if all(word[0].isupper() and word[1:].islower() for word in words if len(word) > 1):
            return True
    
    return False


class DataValidator:
    """
    验证AI提取的数据是否正确
    """
    
    def __init__(self):
        self.client = None
        self._init_openai()
    
    def _init_openai(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
        except Exception as e:
            app_logger.warning(f"OpenAI not available for validation: {e}")
    
    def validate_contact_data(self, contact: Dict) -> Dict:
        """
        验证联系人数据是否正确
        
        Args:
            contact: 联系人信息
            
        Returns:
            Dict with 'valid', 'error', 'corrections'
        """
        name = contact.get('name', '')
        company = contact.get('company', '')
        title = contact.get('title', '')
        
        result = {
            'valid': True,
            'error': None,
            'corrections': {},
            'warnings': []
        }
        
        # 检查1: 人名是否看起来像公司名
        if looks_like_company_name(name):
            result['valid'] = False
            result['error'] = 'name_looks_like_company'
            result['warnings'].append(f"Name '{name}' looks like a company name")
            app_logger.warning(f"Validation: Name looks like company: {name}")
        
        # 检查2: 公司名是否看起来像人名
        if looks_like_person_name(company):
            result['valid'] = False
            result['error'] = 'company_looks_like_person'
            result['warnings'].append(f"Company '{company}' looks like a person name")
            app_logger.warning(f"Validation: Company looks like person: {company}")
        
        # 检查3: 名字和公司是否搞反了
        if not result['valid'] and looks_like_person_name(company) and looks_like_company_name(name):
            # 可能搞反了，建议交换
            result['corrections'] = {
                'swap_name_company': True,
                'suggested_name': company,
                'suggested_company': name
            }
        
        # 检查4: Title是否合理
        suspicious_titles = ['CEO', 'Founder', 'Owner', 'Entrepreneur']
        if any(t in title for t in suspicious_titles):
            result['warnings'].append(f"Title '{title}' may indicate self-employed/scam")
        
        # 检查5: 空值检查
        if not name or len(name) < 2:
            result['valid'] = False
            result['error'] = 'empty_name'
        
        return result
    
    async def validate_with_ai(self, contact: Dict) -> Dict:
        """
        使用AI进行更深入的验证
        
        Args:
            contact: 联系人信息
            
        Returns:
            Dict with validation results
        """
        if not self.client:
            return {'valid': True, 'error': None, 'ai_checked': False}
        
        try:
            prompt = f"""
Verify this LinkedIn contact data for accuracy:

Name: {contact.get('name', 'N/A')}
Company: {contact.get('company', 'N/A')}
Title: {contact.get('title', 'N/A')}

Check for:
1. Is the name a real person's name (not a company)?
2. Is the company a real company (not a person's name)?
3. Does the title make sense for the company?
4. Are there any obvious data extraction errors?

Return JSON only:
{{"valid": true/false, "error": "error_type or null", "corrections": {{"field": "corrected_value"}}}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data validation expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            result['ai_checked'] = True
            
            return result
            
        except Exception as e:
            app_logger.error(f"AI validation failed: {e}")
            return {'valid': True, 'error': None, 'ai_checked': False}
    
    def auto_correct(self, contact: Dict, validation_result: Dict) -> Dict:
        """
        自动纠正数据问题
        
        Args:
            contact: 原始联系人数据
            validation_result: 验证结果
            
        Returns:
            纠正后的联系人数据
        """
        corrected = contact.copy()
        
        # 如果建议交换name和company
        if validation_result.get('corrections', {}).get('swap_name_company'):
            corrected['name'] = validation_result['corrections'].get('suggested_name', contact.get('company', ''))
            corrected['company'] = validation_result['corrections'].get('suggested_company', contact.get('name', ''))
            app_logger.info(f"Auto-corrected: swapped name and company")
        
        # 应用其他纠正
        for field, value in validation_result.get('corrections', {}).items():
            if field in ['suggested_name', 'suggested_company', 'swap_name_company']:
                continue
            if field in corrected:
                corrected[field] = value
                app_logger.info(f"Auto-corrected: {field} = {value}")
        
        return corrected
    
    def validate_batch(self, contacts: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        批量验证联系人
        
        Args:
            contacts: 联系人列表
            
        Returns:
            Tuple of (valid_contacts, invalid_contacts)
        """
        valid = []
        invalid = []
        
        for contact in contacts:
            result = self.validate_contact_data(contact)
            
            if result['valid']:
                valid.append(contact)
            else:
                # 尝试自动纠正
                corrected = self.auto_correct(contact, result)
                
                # 重新验证
                recheck = self.validate_contact_data(corrected)
                if recheck['valid']:
                    valid.append(corrected)
                else:
                    invalid.append({
                        'contact': contact,
                        'error': result['error'],
                        'warnings': result['warnings']
                    })
        
        app_logger.info(f"Batch validation: {len(valid)} valid, {len(invalid)} invalid")
        
        return valid, invalid


# 全局实例
data_validator = DataValidator()


if __name__ == "__main__":
    # 测试
    print("Data Validator Test\n" + "=" * 50)
    
    # 测试数据
    test_contacts = [
        {'name': 'John Smith', 'company': 'Google Inc', 'title': 'Software Engineer'},
        {'name': 'Google Inc', 'company': 'John Smith', 'title': 'Manager'},  # 搞反了
        {'name': 'ACME Technologies', 'company': 'Jane Doe', 'title': 'CEO'},  # 搞反了
        {'name': 'Alice Johnson', 'company': 'Shopify', 'title': 'Product Manager'},
    ]
    
    validator = DataValidator()
    
    for contact in test_contacts:
        print(f"\nChecking: {contact['name']} @ {contact['company']}")
        result = validator.validate_contact_data(contact)
        print(f"  Valid: {result['valid']}")
        if result['error']:
            print(f"  Error: {result['error']}")
        if result['warnings']:
            print(f"  Warnings: {result['warnings']}")
        if result.get('corrections'):
            print(f"  Suggested corrections: {result['corrections']}")
