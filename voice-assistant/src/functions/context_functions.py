import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger
from firebase.firestore_service import FirestoreService
from utils.context_capture import ContextCapture

class ContextFunctions:
    """Context management functions for the voice assistant"""
    
    def __init__(self):
        self.firestore = FirestoreService()
        self.context_capture = ContextCapture()
        self.current_context = {
            "conversation_id": None,
            "user_preferences": {},
            "session_data": {},
            "conversation_history": [],
            "current_window_context": {}
        }
        logger.info("ContextFunctions initialized")
    
    async def set_user_preference(self, preference_key: str, preference_value: str) -> Dict[str, Any]:
        """Set a user preference"""
        try:
            self.current_context["user_preferences"][preference_key] = preference_value
            
            # Save to Firestore if we have a conversation ID
            if self.current_context["conversation_id"]:
                await self.firestore.update_user_preferences(
                    self.current_context["conversation_id"],
                    self.current_context["user_preferences"]
                )
            
            logger.info(f"User preference set: {preference_key} = {preference_value}")
            return {
                "success": True,
                "message": f"Preference '{preference_key}' set to '{preference_value}'",
                "preference_key": preference_key,
                "preference_value": preference_value
            }
            
        except Exception as e:
            logger.error(f"Error setting user preference: {e}")
            return {
                "success": False,
                "message": f"Failed to set preference: {str(e)}"
            }
    
    async def get_user_preference(self, preference_key: str) -> Dict[str, Any]:
        """Get a user preference"""
        try:
            preference_value = self.current_context["user_preferences"].get(preference_key)
            
            if preference_value is not None:
                return {
                    "success": True,
                    "message": f"Preference '{preference_key}' is '{preference_value}'",
                    "preference_key": preference_key,
                    "preference_value": preference_value
                }
            else:
                return {
                    "success": False,
                    "message": f"Preference '{preference_key}' not found",
                    "preference_key": preference_key
                }
                
        except Exception as e:
            logger.error(f"Error getting user preference: {e}")
            return {
                "success": False,
                "message": f"Failed to get preference: {str(e)}"
            }
    
    async def save_conversation_context(self, context_data: str, capture_window_context: bool = True) -> Dict[str, Any]:
        """Save important context from the conversation with optional window context"""
        try:
            # Capture current window context if enabled
            window_context = {}
            if capture_window_context and self.context_capture.is_context_capture_available():
                window_context = self.context_capture.get_context_info()
                self.current_context["current_window_context"] = window_context
            
            context_entry = {
                "timestamp": datetime.now().isoformat(),
                "context": context_data,
                "type": "user_context",
                "window_context": window_context
            }
            
            self.current_context["conversation_history"].append(context_entry)
            
            # Keep only last 50 context entries to prevent memory bloat
            if len(self.current_context["conversation_history"]) > 50:
                self.current_context["conversation_history"] = self.current_context["conversation_history"][-50:]
            
            logger.info(f"Conversation context saved: {context_data[:100]}...")
            return {
                "success": True,
                "message": "Context saved successfully",
                "context_data": context_data
            }
            
        except Exception as e:
            logger.error(f"Error saving conversation context: {e}")
            return {
                "success": False,
                "message": f"Failed to save context: {str(e)}"
            }
    
    async def get_current_window_context(self) -> Dict[str, Any]:
        """Get current window and browser context information"""
        try:
            if not self.context_capture.is_context_capture_available():
                return {
                    "success": False,
                    "message": "Context capture not available - missing dependencies",
                    "dependencies": self.context_capture.get_required_dependencies()
                }
            
            context_info = self.context_capture.get_context_info()
            self.current_context["current_window_context"] = context_info
            
            return {
                "success": True,
                "message": "Current window context captured",
                "context": context_info
            }
            
        except Exception as e:
            logger.error(f"Error getting current window context: {e}")
            return {
                "success": False,
                "message": f"Failed to get window context: {str(e)}"
            }
    
    async def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation context"""
        try:
            history_count = len(self.current_context["conversation_history"])
            preferences_count = len(self.current_context["user_preferences"])
            
            recent_contexts = self.current_context["conversation_history"][-5:] if history_count > 0 else []
            current_window = self.current_context.get("current_window_context", {})
            
            return {
                "success": True,
                "message": f"Conversation has {history_count} context entries and {preferences_count} user preferences",
                "conversation_id": self.current_context["conversation_id"],
                "history_count": history_count,
                "preferences_count": preferences_count,
                "user_preferences": self.current_context["user_preferences"],
                "recent_contexts": recent_contexts,
                "current_window_context": current_window,
                "context_capture_available": self.context_capture.is_context_capture_available()
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {
                "success": False,
                "message": f"Failed to get conversation summary: {str(e)}"
            }
    
    async def clear_session_data(self) -> Dict[str, Any]:
        """Clear temporary session data while keeping user preferences"""
        try:
            self.current_context["session_data"] = {}
            self.current_context["conversation_history"] = []
            
            logger.info("Session data cleared")
            return {
                "success": True,
                "message": "Session data cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"Error clearing session data: {e}")
            return {
                "success": False,
                "message": f"Failed to clear session data: {str(e)}"
            }
    
    async def set_session_variable(self, variable_name: str, variable_value: str) -> Dict[str, Any]:
        """Set a temporary session variable"""
        try:
            self.current_context["session_data"][variable_name] = variable_value
            
            logger.info(f"Session variable set: {variable_name} = {variable_value}")
            return {
                "success": True,
                "message": f"Session variable '{variable_name}' set to '{variable_value}'",
                "variable_name": variable_name,
                "variable_value": variable_value
            }
            
        except Exception as e:
            logger.error(f"Error setting session variable: {e}")
            return {
                "success": False,
                "message": f"Failed to set session variable: {str(e)}"
            }
    
    def initialize_conversation(self, conversation_id: str = None):
        """Initialize a new conversation context"""
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().timestamp()}"
        
        self.current_context["conversation_id"] = conversation_id
        self.current_context["session_data"] = {}
        self.current_context["conversation_history"] = []
        
        logger.info(f"Conversation initialized: {conversation_id}")
        return conversation_id
        
    async def get_status(self, type_filter: str = "all") -> Dict[str, Any]:
        """Get the current status of tasks, reminders, goals, or all"""
        try:
            status_data = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "type": type_filter
            }
            
            # Get tasks status if requested
            if type_filter in ["tasks", "all"]:
                # We'll need to fetch this from Firestore
                tasks = await self.firestore.get_tasks(status="pending")
                status_data["tasks"] = {
                    "count": len(tasks),
                    "pending": tasks
                }
            
            # Get reminders status if requested
            if type_filter in ["reminders", "all"]:
                # We'll need to fetch this from Firestore
                reminders = await self.firestore.get_reminders()
                status_data["reminders"] = {
                    "count": len(reminders),
                    "upcoming": reminders
                }
            
            # Get goals status if requested
            if type_filter in ["goals", "all"]:
                # We'll need to fetch this from Firestore
                goals = await self.firestore.get_goals()
                status_data["goals"] = {
                    "count": len(goals),
                    "active": goals
                }
            
            logger.info(f"Status retrieved for: {type_filter}")
            return status_data
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "success": False,
                "message": f"Failed to get status: {str(e)}"
            }