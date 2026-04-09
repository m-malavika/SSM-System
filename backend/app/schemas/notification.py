from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    student_id: str
    title: str
    message: str
    report_summary: Optional[str] = None
    report_from_date: Optional[str] = None
    report_to_date: Optional[str] = None
    therapy_type: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    student_id: str
    sent_by_user_id: Optional[int] = None
    sent_by_name: Optional[str] = None
    sent_by_role: Optional[str] = None
    title: str
    message: str
    report_summary: Optional[str] = None
    report_from_date: Optional[str] = None
    report_to_date: Optional[str] = None
    therapy_type: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True


class NotificationMarkRead(BaseModel):
    notification_id: int
