# voice-assistant/src/llm/data_models.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Task(BaseModel):
    id: Optional[str] = None # Firestore document ID
    user_id: Optional[str] = None # To associate with a user if multi-user support is added
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: Optional[int] = 0 # e.g., 0: None, 1: Low, 2: Medium, 3: High
    goal_id: Optional[str] = None # Link to a Goal
    context_url: Optional[str] = None
    context_title: Optional[str] = None
    raw_command: Optional[str] = None # The original command that created the task

class Goal(BaseModel):
    id: Optional[str] = None # Firestore document ID
    user_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    target_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: Optional[str] = "active" # e.g., active, completed, on_hold, archived

class Note(BaseModel):
    id: Optional[str] = None # Firestore document ID
    user_id: Optional[str] = None
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    context_url: Optional[str] = None
    context_title: Optional[str] = None
    tags: Optional[List[str]] = []

class Reminder(BaseModel):
    id: Optional[str] = None # Firestore document ID
    user_id: Optional[str] = None
    task_id: Optional[str] = None # Link to a Task
    description: str
    reminder_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    snoozed_until: Optional[datetime] = None
    is_active: bool = True

class Timer(BaseModel):
    id: Optional[str] = None # Firestore document ID
    user_id: Optional[str] = None
    name: Optional[str] = None
    duration_seconds: int
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None # Calculated or set when timer finishes
    is_running: bool = True
    task_id: Optional[str] = None # Optional link to a task for focus sessions

class ConversationTurn(BaseModel):
    id: Optional[str] = None # Firestore document ID
    session_id: str # To group turns within a single interaction session
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_input: Optional[str] = None
    intent: Optional[str] = None
    parameters: Optional[dict] = None
    assistant_response: Optional[str] = None
    context_url: Optional[str] = None
    context_title: Optional[str] = None

# Example usage:
# new_task = Task(description="Finish the report")
# print(new_task.model_dump_json(indent=2))