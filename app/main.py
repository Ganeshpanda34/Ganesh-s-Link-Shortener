from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import string
import random
import httpx
from . import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/shorten")
async def shorten_url(url: str = Form(...), db: Session = Depends(get_db)):
    # Check if URL already exists to avoid duplicates (optional, but good practice)
    # For now, we'll just create a new one every time for simplicity or check if exact match exists
    
    short_code = generate_short_code()
    # Ensure unique short code
    while db.query(models.URLItem).filter(models.URLItem.short_code == short_code).first():
        short_code = generate_short_code()

    db_url = models.URLItem(original_url=url, short_code=short_code)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    # Check if the URL is an image
    is_image = False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(url, timeout=5.0)
            content_type = response.headers.get("content-type", "")
            if content_type.startswith("image/"):
                is_image = True
    except:
        pass # Ignore errors during image check
    
    return {"short_code": short_code, "original_url": url, "is_image": is_image}

@app.get("/proxy-download")
async def proxy_download(url: str):
    async def iterfile():
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
    
    # Get filename from URL or default
    filename = url.split("/")[-1]
    if not filename or "." not in filename:
        filename = "downloaded_image"

    return StreamingResponse(iterfile(), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    db_url = db.query(models.URLItem).filter(models.URLItem.short_code == short_code).first()
    if db_url:
        return RedirectResponse(url=db_url.original_url)
    else:
        raise HTTPException(status_code=404, detail="URL not found")
