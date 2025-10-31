from app import app, db
from models import FestivalEdition, Poll, Polloption, Artists

with app.app_context():
    ed = FestivalEdition(Name="Vicaris Village 2025", Location="Dendermonde")
    db.session.add(ed); db.session.commit()

    p = Poll(Question="Welke artiest wil jij?", festival_id=ed.id)
    db.session.add(p); db.session.commit()

    a1 = Artists(Artist_name="Artist A")
    a2 = Artists(Artist_name="Artist B")
    db.session.add_all([a1, a2]); db.session.commit()

    db.session.add_all([
        Polloption(text="Artist A", artist_id=a1.id, poll_id=p.id),
        Polloption(text="Artist B", artist_id=a2.id, poll_id=p.id),
    ])
    db.session.commit()

print("Seed klaar.")
