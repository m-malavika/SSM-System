from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    # The student_id string (e.g., "STU2025001") — used to find the student user
    student_id = Column(String, nullable=False, index=True)
    # Who sent it
    sent_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    sent_by_name = Column(String, nullable=True)
    sent_by_role = Column(String, nullable=True)
    # Notification content
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    # The AI analysis summary text
    report_summary = Column(Text, nullable=True)
    # Optional: date range of the report
    report_from_date = Column(String, nullable=True)
    report_to_date = Column(String, nullable=True)
    therapy_type = Column(String, nullable=True)
    # Read status
    is_read = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
