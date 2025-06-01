#!/usr/bin/env python3
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger
from firebase.firestore_service import FirestoreService
from utils.context_capture import ContextCapture

class NoteFunctions:
    """Note-taking and management functions for the voice assistant"""
    
    def __init__(self):
        self.firestore = FirestoreService()
        self.context_capture = ContextCapture()
        logger.info("NoteFunctions initialized")
    
    async def take_note(self, content: str, tags: Optional[List[str]] = None, category: str = "general", capture_context: bool = True) -> Dict[str, Any]:
        """Create a new note with optional context capture"""
        try:
            # Capture context information if enabled
            context_info = {}
            if capture_context and self.context_capture.is_context_capture_available():
                context_info = self.context_capture.get_context_info()
                logger.debug(f"Captured context for note: {context_info}")
            
            # Create note data
            note_data = {
                "content": content,
                "category": category,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "context_url": context_info.get("context_url"),
                "context_title": context_info.get("context_title"),
                "window_title": context_info.get("window_title"),
                "process_name": context_info.get("process_name"),
                "is_browser": context_info.get("is_browser", False)
            }
            
            # Save to Firestore
            note_id = await self.firestore.create_note(note_data)
            
            logger.info(f"Created note: {content[:50]}... (ID: {note_id})")
            return {
                "success": True,
                "message": f"Note saved successfully in '{category}' category",
                "note_id": note_id,
                "note_data": note_data
            }
            
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return {
                "success": False,
                "message": "Failed to save note. Please try again."
            }
    
    async def search_notes(self, query: str, category: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search notes by content, category, or tags"""
        try:
            # Build search filters
            filters = {}
            if category:
                filters["category"] = category
            if tags:
                filters["tags"] = tags
            
            # Get notes from Firestore
            notes = await self.firestore.search_notes(query, filters)
            
            if not notes:
                search_desc = f"matching '{query}'"
                if category:
                    search_desc += f" in category '{category}'"
                if tags:
                    search_desc += f" with tags {', '.join(tags)}"
                
                return {
                    "success": True,
                    "message": f"No notes found {search_desc}.",
                    "notes": []
                }
            
            # Format note list for response
            note_list = []
            for note in notes:
                created_date = datetime.fromisoformat(note["created_at"]).strftime("%Y-%m-%d")
                content_preview = note["content"][:100] + "..." if len(note["content"]) > 100 else note["content"]
                note_list.append(f"• [{created_date}] {content_preview} (Category: {note['category']})")
            
            message = f"Found {len(notes)} note(s):\n" + "\n".join(note_list)
            
            logger.info(f"Found {len(notes)} notes matching search")
            return {
                "success": True,
                "message": message,
                "notes": notes
            }
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return {
                "success": False,
                "message": "Failed to search notes. Please try again."
            }
    
    async def list_notes(self, category: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """List recent notes with optional category filter"""
        try:
            # Build filters
            filters = {}
            if category:
                filters["category"] = category
            
            # Get notes from Firestore
            notes = await self.firestore.get_notes(filters, limit=limit)
            
            if not notes:
                category_desc = f" in category '{category}'" if category else ""
                return {
                    "success": True,
                    "message": f"No notes found{category_desc}.",
                    "notes": []
                }
            
            # Format note list for response
            note_list = []
            for note in notes:
                created_date = datetime.fromisoformat(note["created_at"]).strftime("%Y-%m-%d %H:%M")
                content_preview = note["content"][:80] + "..." if len(note["content"]) > 80 else note["content"]
                note_list.append(f"• [{created_date}] {content_preview}")
            
            category_desc = f" in category '{category}'" if category else ""
            message = f"Recent notes{category_desc}:\n" + "\n".join(note_list)
            
            logger.info(f"Listed {len(notes)} notes")
            return {
                "success": True,
                "message": message,
                "notes": notes
            }
            
        except Exception as e:
            logger.error(f"Error listing notes: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve notes. Please try again."
            }
    
    async def update_note(self, note_id: str, content: Optional[str] = None, category: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update an existing note"""
        try:
            # Build update data
            update_data = {
                "updated_at": datetime.now().isoformat()
            }
            
            if content is not None:
                update_data["content"] = content
            if category is not None:
                update_data["category"] = category
            if tags is not None:
                update_data["tags"] = tags
            
            # Update in Firestore
            await self.firestore.update_note(note_id, update_data)
            
            logger.info(f"Updated note {note_id}")
            return {
                "success": True,
                "message": "Note updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating note: {e}")
            return {
                "success": False,
                "message": "Failed to update note. Please try again."
            }
    
    async def delete_note(self, note_id: str) -> Dict[str, Any]:
        """Delete a note"""
        try:
            await self.firestore.delete_note(note_id)
            
            logger.info(f"Deleted note {note_id}")
            return {
                "success": True,
                "message": "Note deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            return {
                "success": False,
                "message": "Failed to delete note. Please try again."
            }
    
    async def list_categories(self) -> Dict[str, Any]:
        """List all note categories"""
        try:
            categories = await self.firestore.get_note_categories()
            
            if not categories:
                return {
                    "success": True,
                    "message": "No note categories found.",
                    "categories": []
                }
            
            # Format category list
            category_list = [f"• {cat}" for cat in categories]
            message = f"Note categories:\n" + "\n".join(category_list)
            
            logger.info(f"Listed {len(categories)} categories")
            return {
                "success": True,
                "message": message,
                "categories": categories
            }
            
        except Exception as e:
            logger.error(f"Error listing categories: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve categories. Please try again."
            }
    
    async def get_note_stats(self) -> Dict[str, Any]:
        """Get statistics about notes"""
        try:
            stats = await self.firestore.get_note_statistics()
            
            message = f"Note Statistics:\n"
            message += f"• Total notes: {stats.get('total_notes', 0)}\n"
            message += f"• Categories: {stats.get('total_categories', 0)}\n"
            message += f"• Notes this week: {stats.get('notes_this_week', 0)}\n"
            message += f"• Most used category: {stats.get('top_category', 'N/A')}"
            
            logger.info("Retrieved note statistics")
            return {
                "success": True,
                "message": message,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting note stats: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve note statistics. Please try again."
            }