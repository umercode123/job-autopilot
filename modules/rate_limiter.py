"""
Rate Limiter for LinkedIn Automation
每日限流控制，持久化存储
"""
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict

from modules.logger_config import app_logger


class RateLimiter:
    """
    每日限流控制，持久化存储
    """
    def __init__(self, state_file: str = 'data/rate_limit_state.json'):
        self.state_file = Path(state_file)
        self.daily_limit = 20  # LinkedIn每日连接限制
        self.note_limit = 5    # 每天带note的连接限制
        self._load_state()
    
    def _load_state(self):
        """加载限流状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                # 检查是否是新的一天
                if self.state.get('date') != str(date.today()):
                    app_logger.info("New day detected, resetting rate limits")
                    self._reset_daily()
            except Exception as e:
                app_logger.error(f"Failed to load rate limit state: {e}")
                self._reset_daily()
        else:
            self._reset_daily()
    
    def _reset_daily(self):
        """重置每日计数"""
        self.state = {
            'date': str(date.today()),
            'connections_sent': 0,
            'notes_sent': 0,
            'last_contact_id': None,
            'reset_time': datetime.now().isoformat()
        }
        self._save_state()
        app_logger.info(f"Rate limits reset for {date.today()}")
    
    def _save_state(self):
        """保存状态到文件"""
        try:
            self.state_file.parent.mkdir(exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            app_logger.error(f"Failed to save rate limit state: {e}")
    
    def can_send_connection(self) -> bool:
        """检查是否可以发送连接请求"""
        return self.state['connections_sent'] < self.daily_limit
    
    def can_send_note(self) -> bool:
        """检查是否可以发送带note的连接"""
        return self.state['notes_sent'] < self.note_limit
    
    def record_connection(self, contact_id: str = None):
        """记录一次连接请求"""
        self.state['connections_sent'] += 1
        self.state['last_contact_id'] = contact_id
        self._save_state()
        app_logger.info(f"Connection recorded: {self.state['connections_sent']}/{self.daily_limit}")
    
    def record_note(self):
        """记录一次带note的连接"""
        self.state['notes_sent'] += 1
        self._save_state()
        app_logger.info(f"Note recorded: {self.state['notes_sent']}/{self.note_limit}")
    
    def get_remaining(self) -> Dict[str, int]:
        """获取剩余配额"""
        return {
            'connections': self.daily_limit - self.state['connections_sent'],
            'notes': self.note_limit - self.state['notes_sent']
        }
    
    def get_status(self) -> Dict:
        """获取完整状态"""
        return {
            **self.state,
            'remaining_connections': self.daily_limit - self.state['connections_sent'],
            'remaining_notes': self.note_limit - self.state['notes_sent'],
            'daily_limit': self.daily_limit,
            'note_limit': self.note_limit
        }


# 全局实例
rate_limiter = RateLimiter()


if __name__ == "__main__":
    # 测试
    print("Rate Limiter Status:")
    print(json.dumps(rate_limiter.get_status(), indent=2))
