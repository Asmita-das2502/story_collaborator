import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

   
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="sender")

    def __repr__(self):
        return f"<User name={self.name}>"


class StoryRoom(Base):
    __tablename__ = "story_rooms"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g. "Our Fantasy Novel"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


    messages: Mapped[list["Message"]] = relationship("Message", back_populates="room")
    chapters: Mapped[list["Chapter"]] = relationship("Chapter", back_populates="room")

    def __repr__(self):
        return f"<StoryRoom name={self.name}>"

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    room_id: Mapped[str] = mapped_column(String, ForeignKey("story_rooms.id"), nullable=False)
    sender_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # The actual message text
    fed_to_cognee: Mapped[bool] = mapped_column(default=False)  # Track what's been ingested
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    room: Mapped["StoryRoom"] = relationship("StoryRoom", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="messages")

    def __repr__(self):
        return f"<Message sender={self.sender_id} content={self.content[:40]}>"


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    room_id: Mapped[str] = mapped_column(String, ForeignKey("story_rooms.id"), nullable=False)
    chapter_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=True)  # Optional chapter title
    content: Mapped[str] = mapped_column(Text, nullable=False)      # The actual chapter text
    is_draft: Mapped[bool] = mapped_column(default=True)            # True = AI draft, False = reviewed/final
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    room: Mapped["StoryRoom"] = relationship("StoryRoom", back_populates="chapters")

    def __repr__(self):
        return f"<Chapter number={self.chapter_number} title={self.title} draft={self.is_draft}>"