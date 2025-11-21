"""
Database Schemas for Readverse (books, manga, novels, ebooks)

Each Pydantic model maps to a MongoDB collection using the lowercase
class name as the collection name.

Examples:
- User -> "user"
- Book -> "book"
- Shelf -> "shelf"
- Review -> "review"
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class User(BaseModel):
    handle: str = Field(..., description="Public username/handle")
    email: str = Field(..., description="Email address")
    avatar_url: Optional[str] = Field(None, description="Profile avatar")
    bio: Optional[str] = Field(None, description="Short bio")
    favorite_genres: List[str] = Field(default_factory=list, description="Genres the user likes")


class Book(BaseModel):
    title: str = Field(..., description="Title of the work")
    creator: str = Field(..., description="Author or artist")
    kind: str = Field(..., description="book | manga | light-novel | ebook")
    cover_url: Optional[str] = Field(None, description="Cover image URL")
    description: Optional[str] = Field(None, description="Short description")
    genres: List[str] = Field(default_factory=list)
    moods: List[str] = Field(default_factory=list)
    total_pages: Optional[int] = Field(None, ge=1, description="Total pages/chapters")
    tags: List[str] = Field(default_factory=list)


class Shelf(BaseModel):
    user_id: str = Field(..., description="Owner user id")
    name: str = Field(..., description="Shelf name, e.g., 'To Read', 'Favorites'")
    description: Optional[str] = None
    book_ids: List[str] = Field(default_factory=list, description="Books on this shelf")


class ReadingProgress(BaseModel):
    user_id: str
    book_id: str
    current_page: int = Field(0, ge=0)
    total_pages: Optional[int] = Field(None, ge=1)
    started_on: Optional[date] = None
    finished_on: Optional[date] = None
    status: str = Field("reading", description="reading | paused | completed | planned")


class Review(BaseModel):
    user_id: str
    book_id: str
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    body: Optional[str] = None


class Quote(BaseModel):
    user_id: str
    book_id: str
    text: str
    page: Optional[int] = Field(None, ge=1)


class Club(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: str
    member_ids: List[str] = Field(default_factory=list)


class Post(BaseModel):
    club_id: str
    user_id: str
    content: str

