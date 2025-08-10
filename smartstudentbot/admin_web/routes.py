from fastapi import APIRouter, Request, Response, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer, BadSignature

from smartstudentbot.config import ADMIN_DASHBOARD_PASSWORD, SESSION_SECRET_KEY
from smartstudentbot.utils.db_utils import get_all_users, get_all_news, save_news, get_news_by_id, update_news, delete_news_by_id
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="smartstudentbot/admin_web/templates")

serializer = URLSafeSerializer(SESSION_SECRET_KEY)

def get_current_admin(request: Request):
    session_cookie = request.cookies.get("admin_session")
    if session_cookie:
        try:
            data = serializer.loads(session_cookie)
            if data.get("is_admin"):
                return data
        except BadSignature:
            return None
    return None

@router.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    if password == ADMIN_DASHBOARD_PASSWORD:
        response = RedirectResponse(url=request.url_for('dashboard_page'), status_code=status.HTTP_302_FOUND)
        session_data = serializer.dumps({"is_admin": True})
        response.set_cookie(key="admin_session", value=session_data, httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url=request.url_for('login_page'))
    response.delete_cookie(key="admin_session")
    return response

@router.post("/add-news")
async def add_news_submit(request: Request, title: str = Form(...), content: str = Form(...), admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'), status_code=status.HTTP_303_SEE_OTHER)

    news_item = {
        "title": title,
        "content": content,
        "file": None,
        "timestamp": str(datetime.now())
    }
    await save_news(news_item)
    return RedirectResponse(url=request.url_for('dashboard_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/edit-news/{news_id}", response_class=HTMLResponse)
async def edit_news_page(request: Request, news_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    news_item = await get_news_by_id(news_id)
    if not news_item:
        return Response("News not found", status_code=404)

    return templates.TemplateResponse("edit_news.html", {"request": request, "news": news_item})

@router.post("/edit-news/{news_id}")
async def edit_news_submit(request: Request, news_id: int, title: str = Form(...), content: str = Form(...), admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    await update_news(news_id, title, content)
    return RedirectResponse(url=request.url_for('dashboard_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/delete-news/{news_id}")
async def delete_news_submit(request: Request, news_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    await delete_news_by_id(news_id)
    return RedirectResponse(url=request.url_for('dashboard_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/dashboard", response_class=HTMLResponse, name="dashboard_page")
async def dashboard_page(request: Request, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    users = await get_all_users()
    news = await get_all_news()
    return templates.TemplateResponse("dashboard.html", {"request": request, "users": users, "news": news})
