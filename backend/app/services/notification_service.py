"""Notification service — creates and manages in-app notifications."""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:
    @staticmethod
    async def create(
        db: AsyncSession, user_id: int, title: str, message: str,
        notification_type: str, reference_id: Optional[int] = None,
        reference_path: Optional[str] = None,
    ) -> Notification:
        n = Notification(
            user_id=user_id, title=title, message=message,
            notification_type=notification_type, reference_id=reference_id,
            reference_path=reference_path, is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(n)
        await db.commit()
        await db.refresh(n)
        return n

    @staticmethod
    async def list_for_user(
        db: AsyncSession, user_id: int, unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        q = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.is_read == False)  # noqa: E712
        q = q.order_by(Notification.created_at.desc()).limit(50)
        res = await db.execute(q)
        return [
            {"id": n.id, "title": n.title, "message": n.message,
             "notification_type": n.notification_type, "reference_id": n.reference_id,
             "reference_path": n.reference_path, "is_read": n.is_read,
             "created_at": n.created_at.isoformat()}
            for n in res.scalars().all()
        ]

    @staticmethod
    async def unread_count(db: AsyncSession, user_id: int) -> int:
        res = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id, Notification.is_read == False  # noqa: E712
            )
        )
        return res.scalar() or 0

    @staticmethod
    async def mark_read(db: AsyncSession, user_id: int, notification_id: Optional[int] = None) -> int:
        from sqlalchemy import update as sa_update
        if notification_id:
            await db.execute(
                sa_update(Notification)
                .where(Notification.user_id == user_id, Notification.id == notification_id)
                .values(is_read=True)
            )
        else:
            await db.execute(
                sa_update(Notification)
                .where(Notification.user_id == user_id)
                .values(is_read=True)
            )
        await db.commit()
        return 1
