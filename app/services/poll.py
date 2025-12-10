from __future__ import annotations

from datetime import date
from models import db, Poll, FestivalEdition


def get_active_festival() -> FestivalEdition:
    """Zoek de actieve festivaleditie, of maak er één aan als er nog geen is."""
    festival = (
        FestivalEdition.query
        .filter_by(is_active=True)
        .order_by(FestivalEdition.Start_date.desc())
        .first()
    )

    if not festival:
        # Fallback: simpele default-editie aanmaken
        festival = FestivalEdition(
            Name="Vicaris Village 2025",
            Location="Vicaris Village",
            Start_date=date(2025, 6, 1),
            End_date=date(2025, 6, 2),
            is_active=True,
        )
        db.session.add(festival)
        db.session.commit()

    return festival


def get_or_create_poll_for_edition(edition: FestivalEdition | int | None) -> Poll | None:
    """
    Zoek of maak de poll die hoort bij een bepaalde editie.

    Geeft ``None`` terug als er geen geldige editie werd meegegeven.
    """

    if not edition:
        return None

    if isinstance(edition, int):
        edition = db.session.get(FestivalEdition, edition)

    if not edition:
        return None

    poll = (
        Poll.query
        .filter_by(festival_id=edition.id)
        .order_by(Poll.id.desc())
        .first()
    )

    if not poll:
        poll = Poll(
            Question="Op welke artiest wil jij stemmen?",
            is_visible=True,
            show_results=True,
            festival_id=edition.id,
        )
        db.session.add(poll)
        db.session.commit()

    return poll

def get_or_create_active_poll() -> Poll:
    """Zoek of maak de poll die hoort bij de actieve editie."""
    festival = get_active_festival()
    return get_or_create_poll_for_edition(festival)