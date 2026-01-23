"""
Checkpoint Manager for LinkedIn Automation
保存处理进度，支持中断恢复
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from modules.logger_config import app_logger


class Checkpoint:
    """
    保存处理进度，支持中断恢复
    """
    def __init__(self, checkpoint_file: str = 'data/checkpoint.json'):
        self.checkpoint_file = Path(checkpoint_file)
        self._load()
    
    def _load(self):
        """加载检查点"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                app_logger.info(f"Loaded checkpoint: {len(self.state.get('processed_contacts', []))} processed")
            except Exception as e:
                app_logger.error(f"Failed to load checkpoint: {e}")
                self._init_state()
        else:
            self._init_state()
    
    def _init_state(self):
        """初始化状态"""
        self.state = {
            'current_company': None,
            'current_school': None,
            'processed_contacts': [],
            'pending_contacts': [],
            'last_updated': None,
            'session_start': datetime.now().isoformat()
        }
    
    def save(self):
        """保存检查点"""
        try:
            self.checkpoint_file.parent.mkdir(exist_ok=True)
            self.state['last_updated'] = datetime.now().isoformat()
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
            app_logger.debug("Checkpoint saved")
        except Exception as e:
            app_logger.error(f"Failed to save checkpoint: {e}")
    
    def set_current_search(self, company: str, school: str):
        """设置当前搜索目标"""
        self.state['current_company'] = company
        self.state['current_school'] = school
        self.save()
    
    def mark_contact_processed(self, contact_id: str):
        """标记联系人已处理"""
        if contact_id not in self.state['processed_contacts']:
            self.state['processed_contacts'].append(contact_id)
        self._remove_from_pending(contact_id)
        self.save()
        app_logger.debug(f"Contact processed: {contact_id}")
    
    def _remove_from_pending(self, contact_id: str):
        """从pending列表移除"""
        self.state['pending_contacts'] = [
            c for c in self.state['pending_contacts'] 
            if c != contact_id
        ]
    
    def set_pending_contacts(self, contacts: List[Dict]):
        """设置待处理联系人列表"""
        self.state['pending_contacts'] = [
            c.get('linkedin_url') or c.get('name', '') 
            for c in contacts
        ]
        self.save()
        app_logger.info(f"Set {len(contacts)} pending contacts")
    
    def get_resume_point(self) -> List[str]:
        """获取需要恢复处理的联系人ID列表"""
        pending = self.state.get('pending_contacts', [])
        processed = self.state.get('processed_contacts', [])
        return [c for c in pending if c not in processed]
    
    def is_contact_processed(self, contact_id: str) -> bool:
        """检查联系人是否已处理"""
        return contact_id in self.state.get('processed_contacts', [])
    
    def has_pending_work(self) -> bool:
        """检查是否有未完成的工作"""
        return len(self.get_resume_point()) > 0
    
    def get_progress(self) -> Dict:
        """获取进度统计"""
        total = len(self.state.get('pending_contacts', []))
        processed = len(self.state.get('processed_contacts', []))
        remaining = len(self.get_resume_point())
        
        return {
            'total': total,
            'processed': processed,
            'remaining': remaining,
            'current_company': self.state.get('current_company'),
            'current_school': self.state.get('current_school'),
            'last_updated': self.state.get('last_updated')
        }
    
    def clear(self):
        """清空检查点（开始新会话）"""
        self._init_state()
        self.save()
        app_logger.info("Checkpoint cleared")
    
    def clear_processed(self):
        """只清空已处理列表（保留pending）"""
        self.state['processed_contacts'] = []
        self.save()


# 全局实例
checkpoint = Checkpoint()


if __name__ == "__main__":
    print("Checkpoint Status:")
    print(json.dumps(checkpoint.get_progress(), indent=2))
