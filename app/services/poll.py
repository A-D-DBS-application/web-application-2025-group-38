from __future__ import annotations

from models import db, Poll


def get_or_create_active_poll() -> Poll:
    poll = Poll.query.order_by(Poll.id).first()
    if not poll:
        poll = Poll(
            Question="Festival poll",
            is_visible=True,
            show_results=True,
        )
        db.session.add(poll)
        db.session.commit()
    return poll