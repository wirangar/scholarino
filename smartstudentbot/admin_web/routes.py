from fastapi import APIRouter, Request, Response, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer, BadSignature

from smartstudentbot.config import ADMIN_DASHBOARD_PASSWORD, SESSION_SECRET_KEY
from smartstudentbot.utils.db_utils import get_all_users, get_all_news, save_news, get_news_by_id, update_news, delete_news_by_id, get_all_stories, approve_story
from smartstudentbot.utils.json_utils import read_json_file, add_item_to_json, get_item_by_id, update_item_in_json, delete_item_from_json
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="smartstudentbot/admin_web/templates")

QNA_FILE_PATH = "smartstudentbot/qna.json"
DISCOUNTS_FILE_PATH = "smartstudentbot/discounts.json"
LEARNING_FILE_PATH = "smartstudentbot/italian_learning_resources.json"

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

@router.post("/approve-story/{story_id}")
async def approve_story_submit(request: Request, story_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    await approve_story(story_id)
    return RedirectResponse(url=request.url_for('dashboard_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/dashboard", response_class=HTMLResponse, name="dashboard_page")
async def dashboard_page(request: Request, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    users = await get_all_users()
    news = await get_all_news()
    stories = await get_all_stories()
    return templates.TemplateResponse("dashboard.html", {"request": request, "users": users, "news": news, "stories": stories})

@router.get("/qna", response_class=HTMLResponse, name="qna_page")
async def qna_page(request: Request, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    qna_data = read_json_file(QNA_FILE_PATH)
    return templates.TemplateResponse("qna.html", {"request": request, "qna_data": qna_data.get("data", [])})

@router.post("/qna/add", name="add_qna")
async def add_qna(request: Request, question: str = Form(...), answer: str = Form(...), admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    new_qna = {"q": question, "a": answer}
    add_item_to_json(QNA_FILE_PATH, new_qna)

    return RedirectResponse(url=request.url_for('qna_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/qna/edit/{item_id}", response_class=HTMLResponse, name="edit_qna_page")
async def edit_qna_page(request: Request, item_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    item = get_item_by_id(QNA_FILE_PATH, item_id)
    if not item:
        return Response("Item not found", status_code=404)

    return templates.TemplateResponse("edit_qna.html", {"request": request, "item": item})

@router.post("/qna/edit/{item_id}", name="edit_qna")
async def edit_qna(request: Request, item_id: int, question: str = Form(...), answer: str = Form(...), admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    updated_data = {"q": question, "a": answer}
    update_item_in_json(QNA_FILE_PATH, item_id, updated_data)

    return RedirectResponse(url=request.url_for('qna_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/qna/delete/{item_id}", name="delete_qna")
async def delete_qna(request: Request, item_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    delete_item_from_json(QNA_FILE_PATH, item_id)

    return RedirectResponse(url=request.url_for('qna_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/discounts", response_class=HTMLResponse, name="discounts_page")
async def discounts_page(request: Request, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    discounts_data = read_json_file(DISCOUNTS_FILE_PATH)
    return templates.TemplateResponse("discounts.html", {"request": request, "discounts_data": discounts_data.get("data", [])})

@router.post("/discounts/add", name="add_discount")
async def add_discount(request: Request, store: str = Form(...), offer: str = Form(...), conditions: str = Form(...), admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    new_discount = {"store": store, "offer": offer, "conditions": conditions}
    add_item_to_json(DISCOUNTS_FILE_PATH, new_discount)

    return RedirectResponse(url=request.url_for('discounts_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/discounts/edit/{item_id}", response_class=HTMLResponse, name="edit_discount_page")
async def edit_discount_page(request: Request, item_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    item = get_item_by_id(DISCOUNTS_FILE_PATH, item_id)
    if not item:
        return Response("Item not found", status_code=404)

    return templates.TemplateResponse("edit_discount.html", {"request": request, "item": item})

@router.post("/discounts/edit/{item_id}", name="edit_discount")
async def edit_discount(request: Request, item_id: int, store: str = Form(...), offer: str = Form(...), conditions: str = Form(...), admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    updated_data = {"store": store, "offer": offer, "conditions": conditions}
    update_item_in_json(DISCOUNTS_FILE_PATH, item_id, updated_data)

    return RedirectResponse(url=request.url_for('discounts_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/discounts/delete/{item_id}", name="delete_discount")
async def delete_discount(request: Request, item_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    delete_item_from_json(DISCOUNTS_FILE_PATH, item_id)

    return RedirectResponse(url=request.url_for('discounts_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/learning", response_class=HTMLResponse, name="learning_page")
async def learning_page(request: Request, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    learning_data = read_json_file(LEARNING_FILE_PATH)
    return templates.TemplateResponse("learning.html", {"request": request, "learning_data": learning_data.get("data", [])})

@router.post("/learning/add", name="add_learning")
async def add_learning(request: Request, type: str = Form(...), name: str = Form(...), description: str = Form(...), link: str = Form(...), admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    new_resource = {"type": type, "name": name, "description": description, "link": link}
    add_item_to_json(LEARNING_FILE_PATH, new_resource)

    return RedirectResponse(url=request.url_for('learning_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/learning/edit/{item_id}", response_class=HTMLResponse, name="edit_learning_page")
async def edit_learning_page(request: Request, item_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    item = get_item_by_id(LEARNING_FILE_PATH, item_id)
    if not item:
        return Response("Item not found", status_code=404)

    return templates.TemplateResponse("edit_learning.html", {"request": request, "item": item})

@router.post("/learning/edit/{item_id}", name="edit_learning")
async def edit_learning(request: Request, item_id: int, type: str = Form(...), name: str = Form(...), description: str = Form(...), link: str = Form(...), admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    updated_data = {"type": type, "name": name, "description": description, "link": link}
    update_item_in_json(LEARNING_FILE_PATH, item_id, updated_data)

    return RedirectResponse(url=request.url_for('learning_page'), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/learning/delete/{item_id}", name="delete_learning")
async def delete_learning(request: Request, item_id: int, admin: dict = Depends(get_current_admin)):
    if not admin:
        return RedirectResponse(url=request.url_for('login_page'))

    delete_item_from_json(LEARNING_FILE_PATH, item_id)

    return RedirectResponse(url=request.url_for('learning_page'), status_code=status.HTTP_303_SEE_OTHER)
