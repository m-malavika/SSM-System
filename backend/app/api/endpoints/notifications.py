from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.api import deps
from app.models.user import User, UserRole
from app.crud import notification as crud_notification
from app.schemas.notification import NotificationCreate, NotificationResponse, NotificationMarkRead

router = APIRouter()


@router.post("/send-report", response_model=NotificationResponse)
def send_report_to_parent(
    *,
    db: Session = Depends(deps.get_db),
    notification_in: NotificationCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send an AI analysis report to the student/parent user.
    Only admin, teacher, or therapist can send reports.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER, UserRole.THERAPIST, "admin", "teacher", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin, teacher, or therapist can send reports to parents"
        )
    
    try:
        notification = crud_notification.create(
            db,
            obj_in=notification_in,
            sent_by_user_id=current_user.id,
            sent_by_name=current_user.username,
            sent_by_role=current_user.role if isinstance(current_user.role, str) else current_user.role.value,
        )
        logging.info(f"Report sent to student {notification_in.student_id} by {current_user.username}")
        return notification
    except Exception as e:
        logging.error(f"Error sending report notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send report: {str(e)}"
        )


@router.get("/my-notifications", response_model=List[NotificationResponse])
def get_my_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all notifications for the current student user.
    The username is the student_id.
    """
    return crud_notification.get_by_student_id(db, student_id=current_user.username)


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get unread notification count for current student user."""
    count = crud_notification.get_unread_count(db, student_id=current_user.username)
    return {"unread_count": count}


@router.post("/mark-read")
def mark_notification_read(
    *,
    db: Session = Depends(deps.get_db),
    body: NotificationMarkRead,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Mark a single notification as read."""
    notification = crud_notification.mark_as_read(db, notification_id=body.notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok"}


@router.post("/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Mark all notifications as read for the current student user."""
    crud_notification.mark_all_read(db, student_id=current_user.username)
    return {"status": "ok"}
