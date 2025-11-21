import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Book, Shelf, ReadingProgress, Review, Quote, Club, Post, User


app = FastAPI(title="Readverse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class IdModel(BaseModel):
    id: str


def to_public(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    d = dict(doc)
    if d.get("_id") is not None:
        d["id"] = str(d.pop("_id"))
    # Convert datetime to isoformat
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


@app.get("/")
def read_root():
    return {"message": "Readverse backend ready"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
    except Exception as e:
        response["database"] = f"⚠️ {str(e)[:80]}"
    return response


# ---------- Users (minimal) ----------
@app.post("/users", response_model=IdModel)
def create_user(user: User):
    new_id = create_document("user", user)
    return {"id": new_id}


@app.get("/users")
def list_users(handle: Optional[str] = None):
    filt = {"handle": handle} if handle else {}
    docs = get_documents("user", filt, limit=100)
    return [to_public(d) for d in docs]


# ---------- Books ----------
@app.post("/books", response_model=IdModel)
def create_book(book: Book):
    new_id = create_document("book", book)
    return {"id": new_id}


@app.get("/books")
def list_books(kind: Optional[str] = None, q: Optional[str] = None, limit: int = Query(100, ge=1, le=200)):
    filt: Dict[str, Any] = {}
    if kind:
        filt["kind"] = kind
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}
    docs = get_documents("book", filt, limit=limit)
    return [to_public(d) for d in docs]


@app.get("/books/{book_id}")
def get_book(book_id: str):
    doc = db["book"].find_one({"_id": oid(book_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Book not found")
    return to_public(doc)


class BookUpdate(BaseModel):
    title: Optional[str] = None
    creator: Optional[str] = None
    kind: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    genres: Optional[List[str]] = None
    moods: Optional[List[str]] = None
    total_pages: Optional[int] = None
    tags: Optional[List[str]] = None


@app.patch("/books/{book_id}")
def update_book(book_id: str, payload: BookUpdate):
    upd = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not upd:
        return {"updated": 0}
    res = db["book"].update_one({"_id": oid(book_id)}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"updated": res.modified_count}


@app.delete("/books/{book_id}")
def delete_book(book_id: str):
    res = db["book"].delete_one({"_id": oid(book_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"deleted": 1}


# ---------- Shelves ----------
@app.post("/shelves", response_model=IdModel)
def create_shelf(shelf: Shelf):
    new_id = create_document("shelf", shelf)
    return {"id": new_id}


@app.get("/shelves")
def list_shelves(user_id: Optional[str] = None):
    filt = {"user_id": user_id} if user_id else {}
    docs = get_documents("shelf", filt, limit=200)
    return [to_public(d) for d in docs]


@app.post("/shelves/{shelf_id}/add")
def shelf_add_book(shelf_id: str, book_id: str):
    res = db["shelf"].update_one({"_id": oid(shelf_id)}, {"$addToSet": {"book_ids": book_id}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shelf not found")
    return {"ok": True}


# ---------- Reading Progress ----------
@app.post("/progress", response_model=IdModel)
def create_progress(p: ReadingProgress):
    new_id = create_document("readingprogress", p)
    return {"id": new_id}


@app.get("/progress")
def get_progress(user_id: Optional[str] = None, book_id: Optional[str] = None):
    filt: Dict[str, Any] = {}
    if user_id:
        filt["user_id"] = user_id
    if book_id:
        filt["book_id"] = book_id
    docs = get_documents("readingprogress", filt, limit=500)
    return [to_public(d) for d in docs]


class ProgressUpdate(BaseModel):
    current_page: Optional[int] = None
    status: Optional[str] = None
    total_pages: Optional[int] = None


@app.patch("/progress/{progress_id}")
def update_progress(progress_id: str, upd: ProgressUpdate):
    data = {k: v for k, v in upd.model_dump(exclude_none=True).items()}
    if not data:
        return {"updated": 0}
    res = db["readingprogress"].update_one({"_id": oid(progress_id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Progress not found")
    return {"updated": res.modified_count}


# ---------- Reviews ----------
@app.post("/reviews", response_model=IdModel)
def create_review(r: Review):
    new_id = create_document("review", r)
    return {"id": new_id}


@app.get("/reviews")
def list_reviews(book_id: Optional[str] = None):
    filt = {"book_id": book_id} if book_id else {}
    docs = get_documents("review", filt, limit=200)
    return [to_public(d) for d in docs]


# ---------- Quotes ----------
@app.post("/quotes", response_model=IdModel)
def create_quote(q: Quote):
    new_id = create_document("quote", q)
    return {"id": new_id}


@app.get("/quotes")
def list_quotes(user_id: Optional[str] = None, book_id: Optional[str] = None):
    filt: Dict[str, Any] = {}
    if user_id:
        filt["user_id"] = user_id
    if book_id:
        filt["book_id"] = book_id
    docs = get_documents("quote", filt, limit=200)
    return [to_public(d) for d in docs]


# ---------- Clubs & Posts ----------
@app.post("/clubs", response_model=IdModel)
def create_club(c: Club):
    new_id = create_document("club", c)
    return {"id": new_id}


@app.get("/clubs")
def list_clubs():
    docs = get_documents("club", {}, limit=200)
    return [to_public(d) for d in docs]


@app.post("/posts", response_model=IdModel)
def create_post(p: Post):
    new_id = create_document("post", p)
    return {"id": new_id}


@app.get("/posts")
def list_posts(club_id: Optional[str] = None):
    filt = {"club_id": club_id} if club_id else {}
    docs = get_documents("post", filt, limit=500)
    return [to_public(d) for d in docs]


# ---------- Simple recommendations (stub) ----------
@app.get("/recommendations")
def recommendations(genre: Optional[str] = None, user_id: Optional[str] = None):
    """Very simple content-based recs: return popular genres or recent additions."""
    filt: Dict[str, Any] = {}
    if genre:
        filt["genres"] = genre
    # Get up to 12 books as recommendations
    docs = db["book"].find(filt).sort("created_at", -1).limit(12)
    return [to_public(d) for d in docs]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
