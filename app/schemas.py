from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Название задачи (не пустое)")
    description: Optional[str] = Field(None, description="Подробное описание задачи")
    is_completed: bool = Field(default=False, description="Статус выполнения задачи")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Название задачи")
    description: Optional[str] = Field(None, description="Подробное описание задачи")
    is_completed: Optional[bool] = Field(None, description="Статус выполнения задачи")

class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
