import os
import sys
from typing import Optional, Dict, Any
from loguru import logger

try:
    import win32gui
    import win32process
    import psutil
    WINDOWS_LIBS_AVAILABLE = True
except ImportError:
    WINDOWS_LIBS_AVAILABLE = False
    logger.warning("Windows libraries (pywin32, psutil) not available. Context capture will be limited.")

try:
    from pywinauto import Application
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    logger.warning("pywinauto not available. Browser URL capture will be disabled.")

class ContextCapture:
    """Captures contextual information about the active window and browser state"""
    
    def __init__(self):
        self.supported_browsers = {
            'chrome.exe': 'Chrome',
            'msedge.exe': 'Edge',
            'firefox.exe': 'Firefox',
            'brave.exe': 'Brave',
            'opera.exe': 'Opera'
        }
        logger.info("ContextCapture initialized")
    
    def get_active_window_info(self) -> Dict[str, Any]:
        """Get information about the currently active window"""
        if not WINDOWS_LIBS_AVAILABLE:
            return {
                "success": False,
                "error": "Windows libraries not available",
                "window_title": None,
                "process_name": None,
                "is_browser": False
            }
        
        try:
            # Get the active window handle
            window = win32gui.GetForegroundWindow()
            
            # Get window title
            window_title = win32gui.GetWindowText(window)
            
            # Get process information
            _, pid = win32process.GetWindowThreadProcessId(window)
            process = psutil.Process(pid)
            process_name = process.name().lower()
            
            # Check if it's a browser
            is_browser = process_name in self.supported_browsers
            browser_name = self.supported_browsers.get(process_name) if is_browser else None
            
            logger.debug(f"Active window: {window_title} ({process_name})")
            
            return {
                "success": True,
                "window_title": window_title,
                "process_name": process_name,
                "browser_name": browser_name,
                "is_browser": is_browser,
                "pid": pid
            }
            
        except Exception as e:
            logger.error(f"Error getting active window info: {e}")
            return {
                "success": False,
                "error": str(e),
                "window_title": None,
                "process_name": None,
                "is_browser": False
            }
    
    def get_browser_url(self, browser_name: str = None) -> Optional[str]:
        """Attempt to get the current URL from the active browser"""
        if not PYWINAUTO_AVAILABLE:
            logger.warning("pywinauto not available for browser URL capture")
            return None
        
        try:
            # Get active window info first
            window_info = self.get_active_window_info()
            if not window_info.get("is_browser"):
                return None
            
            detected_browser = window_info.get("browser_name", "").lower()
            
            # Try Chrome/Edge (Chromium-based browsers)
            if detected_browser in ['chrome', 'edge', 'brave', 'opera']:
                return self._get_chromium_url(detected_browser)
            
            # Try Firefox
            elif detected_browser == 'firefox':
                return self._get_firefox_url()
            
            else:
                logger.warning(f"Unsupported browser: {detected_browser}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting browser URL: {e}")
            return None
    
    def _get_chromium_url(self, browser_name: str) -> Optional[str]:
        """Get URL from Chromium-based browsers (Chrome, Edge, Brave, Opera)"""
        try:
            app = Application(backend='uia')
            
            # Connect to the browser window
            if browser_name.lower() == 'chrome':
                app.connect(title_re=".*Chrome.*")
            elif browser_name.lower() == 'edge':
                app.connect(title_re=".*Edge.*")
            elif browser_name.lower() == 'brave':
                app.connect(title_re=".*Brave.*")
            elif browser_name.lower() == 'opera':
                app.connect(title_re=".*Opera.*")
            else:
                app.connect(title_re=f".*{browser_name}.*")
            
            # Get the address bar
            dlg = app.top_window()
            
            # Try different possible names for the address bar
            address_bar_names = [
                "Address and search bar",
                "Address bar",
                "Search or type web address",
                "Omnibox"
            ]
            
            for bar_name in address_bar_names:
                try:
                    url_element = dlg.child_window(title=bar_name, control_type="Edit")
                    url = url_element.get_value()
                    if url and url.startswith(('http://', 'https://')):
                        logger.debug(f"Retrieved URL from {browser_name}: {url}")
                        return url
                except:
                    continue
            
            logger.warning(f"Could not find address bar in {browser_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting URL from {browser_name}: {e}")
            return None
    
    def _get_firefox_url(self) -> Optional[str]:
        """Get URL from Firefox browser"""
        try:
            app = Application(backend='uia')
            app.connect(title_re=".*Firefox.*")
            
            dlg = app.top_window()
            
            # Firefox address bar names
            address_bar_names = [
                "Search or enter address",
                "Address bar",
                "Location bar"
            ]
            
            for bar_name in address_bar_names:
                try:
                    url_element = dlg.child_window(title=bar_name, control_type="Edit")
                    url = url_element.get_value()
                    if url and url.startswith(('http://', 'https://')):
                        logger.debug(f"Retrieved URL from Firefox: {url}")
                        return url
                except:
                    continue
            
            logger.warning("Could not find address bar in Firefox")
            return None
            
        except Exception as e:
            logger.error(f"Error getting URL from Firefox: {e}")
            return None
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get comprehensive context information including window and browser data"""
        try:
            # Get active window information
            window_info = self.get_active_window_info()
            
            context = {
                "timestamp": None,  # Will be set by caller
                "window_title": window_info.get("window_title"),
                "process_name": window_info.get("process_name"),
                "is_browser": window_info.get("is_browser", False),
                "browser_name": window_info.get("browser_name"),
                "context_url": None,
                "context_title": None
            }
            
            # If it's a browser, try to get the URL
            if context["is_browser"]:
                url = self.get_browser_url(context["browser_name"])
                if url:
                    context["context_url"] = url
                    # Extract page title from window title (remove browser name)
                    window_title = context["window_title"] or ""
                    browser_name = context["browser_name"] or ""
                    if browser_name.lower() in window_title.lower():
                        # Remove browser name from title to get page title
                        context["context_title"] = window_title.replace(f" - {browser_name}", "").strip()
                    else:
                        context["context_title"] = window_title
            
            logger.debug(f"Context captured: {context}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting context info: {e}")
            return {
                "timestamp": None,
                "window_title": None,
                "process_name": None,
                "is_browser": False,
                "browser_name": None,
                "context_url": None,
                "context_title": None,
                "error": str(e)
            }
    
    def is_context_capture_available(self) -> bool:
        """Check if context capture functionality is available"""
        return WINDOWS_LIBS_AVAILABLE
    
    def get_required_dependencies(self) -> Dict[str, bool]:
        """Get status of required dependencies"""
        return {
            "pywin32": WINDOWS_LIBS_AVAILABLE,
            "psutil": WINDOWS_LIBS_AVAILABLE,
            "pywinauto": PYWINAUTO_AVAILABLE
        }