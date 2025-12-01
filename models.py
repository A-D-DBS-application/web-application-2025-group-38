# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    email = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, server_default="false", nullable=False)


class Genres(db.Model):
    __tablename__ = "Genres"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    artists = db.relationship(
        "Artists",
        secondary="ArtistGenres",
        back_populates="genres"
    )


class ArtistGenres(db.Model):
    __tablename__ = "ArtistGenres"

    artist_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Artists.id", ondelete="CASCADE"),
        primary_key=True
    )
    genre_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Genres.id", ondelete="CASCADE"),
        primary_key=True
    )


class Artists(db.Model):
    __tablename__ = "Artists"

    id = db.Column(db.BigInteger, primary_key=True)
    created_at = db.Column(db.DateTime)
    Artist_name = db.Column(db.String, unique=True)
    genre = db.Column(db.String)  # OPTIONAL legacy

    # Many-to-Many
    genres = db.relationship(
        "Genres",
        secondary="ArtistGenres",
        back_populates="artists"
    )



class FestivalEdition(db.Model):
    __tablename__ = "FestivalEdition"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    Start_date = db.Column(db.Date)
    End_date = db.Column(db.Date)
    Name = db.Column(db.Text)
    Location = db.Column(db.Text)


class Poll(db.Model):
    __tablename__ = "poll"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    Question = db.Column(db.Text)
    festival_id = db.Column(db.Integer, db.ForeignKey("FestivalEdition.id"))

    festival = db.relationship(FestivalEdition, backref="polls")


class Polloption(db.Model):
    __tablename__ = "Polloption"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    text = db.Column(db.Text)
    Count = db.Column(db.Integer)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artists.id"))
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))

    artist = db.relationship(Artists)
    poll = db.relationship(Poll, backref="options")

    @property
    def image_url(self):
        filename = self.text.lower().replace(" ", "_") + ".jpg"
        return f"images/artist_images/{filename}"


class VotesFor(db.Model):
    __tablename__ = "Votes_for"

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), primary_key=True)
    polloption_id = db.Column(db.Integer, db.ForeignKey("Polloption.id"), primary_key=True)

    user = db.relationship(User)
    option = db.relationship(Polloption)


class SuggestionFeedback(db.Model):
    __tablename__ = "Suggestion_feedback"
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artists.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=True)  
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
