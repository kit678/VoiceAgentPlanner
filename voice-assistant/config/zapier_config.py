# Zapier Integration Configuration
# Replace these placeholder URLs with your actual Zapier webhook URLs

import os
from typing import Dict, Optional

class ZapierConfig:
    """Configuration for Zapier webhook integrations"""
    
    def __init__(self):
        # Load from environment variables or use defaults
        self.webhook_urls = {
            "trello": os.getenv("ZAPIER_TRELLO_WEBHOOK", "https://hooks.zapier.com/hooks/catch/YOUR_TRELLO_WEBHOOK_ID/"),
            "notion": os.getenv("ZAPIER_NOTION_WEBHOOK", "https://hooks.zapier.com/hooks/catch/YOUR_NOTION_WEBHOOK_ID/"),
            "google_calendar": os.getenv("ZAPIER_CALENDAR_WEBHOOK", "https://hooks.zapier.com/hooks/catch/YOUR_CALENDAR_WEBHOOK_ID/"),
            "slack": os.getenv("ZAPIER_SLACK_WEBHOOK", "https://hooks.zapier.com/hooks/catch/YOUR_SLACK_WEBHOOK_ID/")
        }
        
        # Timeout settings
        self.request_timeout = int(os.getenv("ZAPIER_TIMEOUT", "10"))  # seconds
        
        # Retry settings
        self.max_retries = int(os.getenv("ZAPIER_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("ZAPIER_RETRY_DELAY", "2"))  # seconds
    
    def get_webhook_url(self, service: str) -> Optional[str]:
        """Get webhook URL for a specific service"""
        return self.webhook_urls.get(service.lower())
    
    def is_service_configured(self, service: str) -> bool:
        """Check if a service has a valid webhook URL configured"""
        url = self.get_webhook_url(service)
        return url is not None and not url.startswith("https://hooks.zapier.com/hooks/catch/YOUR_")
    
    def get_configured_services(self) -> list:
        """Get list of properly configured services"""
        return [service for service in self.webhook_urls.keys() if self.is_service_configured(service)]

# Global configuration instance
zapier_config = ZapierConfig()