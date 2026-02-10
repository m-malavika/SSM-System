from typing import List
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate


def create(db: Session, *, obj_in: NotificationCreate, sent_by_user_id: int = None, sent_by_name: str = None, sent_by_role: str = None) -> Notification:
    db_obj = Notification(
        student_id=obj_in.student_id,
        sent_by_user_id=sent_by_user_id,
        sent_by_name=sent_by_name,
        sent_by_role=sent_by_role,
        title=obj_in.title,
        message=obj_in.message,
        report_summary=obj_in.report_summary,
        report_from_date=obj_in.report_from_date,
        report_to_date=obj_in.report_to_date,
        therapy_type=obj_in.therapy_type,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_by_student_id(db: Session, student_id: str) -> List[Notification]:
    """Get all notifications for a student (by student_id string like STU2025001)."""
    return (
        db.query(Notification)
        .filter(Notification.student_id == student_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


def mark_as_read(db: Session, notification_id: int) -> Notification:
    db_obj = db.query(Notification).filter(Notification.id == notification_id).first()
    if db_obj:
        db_obj.is_read = True
        db.commit()
        db.refresh(db_obj)
    return db_obj


def mark_all_read(db: Session, student_id: str):
    db.query(Notification).filter(
        Notification.student_id == student_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()


def get_unread_count(db: Session, student_id: str) -> int:
    return (
        db.query(Notification)
        .filter(Notification.student_id == student_id, Notification.is_read == False)
        .count()
    )
