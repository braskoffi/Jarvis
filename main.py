import os
from pathlib import Path
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from dotenv import load_dotenv
from . import database
from .auth import hash_password, verify_password
from .ai import reply
from .actions import propose, confirm

load_dotenv()
app = FastAPI(title="JARVIS 2KR", version="0.1.0")
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")
COOKIE = "jarvis_session"
MAX_AGE = 60*60*24*14

class AuthBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
class ActionBody(BaseModel):
    action_type: str = Field(min_length=1, max_length=60)
    payload: dict = Field(default_factory=dict)
class ConfirmBody(BaseModel):
    action_id: str = Field(min_length=16, max_length=64)

def signer():
    secret = os.getenv("APP_SECRET","")
    if len(secret) < 32 or secret.startswith("replace-with-"):
        raise HTTPException(status_code=500, detail="Configurez APP_SECRET dans .env avec au moins 32 caractères aléatoires.")
    return URLSafeTimedSerializer(secret, salt="jarvis-session")

def set_session(response, uid):
    response.set_cookie(COOKIE, signer().dumps({"uid":uid}), httponly=True, samesite="lax",
                        secure=os.getenv("COOKIE_SECURE","0")=="1", max_age=MAX_AGE, path="/")

def current_user(request):
    token = request.cookies.get(COOKIE)
    if not token: raise HTTPException(status_code=401, detail="Connexion requise.")
    try:
        data = signer().loads(token, max_age=MAX_AGE)
        user = database.get_user_by_id(int(data["uid"]))
    except (BadSignature, SignatureExpired, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Session invalide ou expirée.")
    if not user: raise HTTPException(status_code=401, detail="Compte introuvable.")
    return dict(user)

@app.on_event("startup")
def startup(): database.init_db()

@app.get("/")
def index(): return FileResponse(STATIC/"index.html")

@app.get("/api/health")
def health(): return {"status":"ok","service":"JARVIS 2KR","ai_configured":bool(os.getenv("OPENAI_API_KEY","").strip())}

@app.post("/api/register")
def register(body: AuthBody, response: Response):
    email = str(body.email).strip().lower()
    try: uid = database.create_user(email, hash_password(body.password))
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc): raise HTTPException(409, "Cette adresse e-mail est déjà utilisée.")
        raise
    set_session(response, uid)
    return {"ok":True,"user":{"id":uid,"email":email}}

@app.post("/api/login")
def login(body: AuthBody, response: Response):
    user = database.get_user_by_email(str(body.email).strip().lower())
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Adresse e-mail ou mot de passe incorrect.")
    set_session(response, int(user["id"]))
    return {"ok":True,"user":{"id":int(user["id"]),"email":user["email"]}}

@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE, path="/", httponly=True, samesite="lax")
    return {"ok":True}

@app.get("/api/me")
def me(request: Request): return {"user":current_user(request)}

@app.get("/api/messages")
def messages(request: Request): return {"messages":database.get_messages(current_user(request)["id"])}

@app.delete("/api/messages")
def clear(request: Request):
    database.clear_messages(current_user(request)["id"])
    return {"ok":True}

@app.post("/api/chat")
def chat(body: ChatBody, request: Request):
    user = current_user(request)
    content = body.message.strip()
    if not content: raise HTTPException(422, "Message vide.")
    history = database.get_messages(user["id"], 30)
    database.add_message(user["id"], "user", content)
    context = [{"role":m["role"],"content":m["content"]} for m in history]
    context.append({"role":"user","content":content})
    answer = reply(context)
    database.add_message(user["id"], "assistant", answer)
    return {"reply":answer}

@app.post("/api/actions/propose")
def propose_action(body: ActionBody, request: Request):
    try: return propose(current_user(request)["id"], body.action_type, body.payload)
    except ValueError as exc: raise HTTPException(400, str(exc))

@app.post("/api/actions/confirm")
def confirm_action(body: ConfirmBody, request: Request):
    try: return confirm(current_user(request)["id"], body.action_id)
    except ValueError as exc: raise HTTPException(404, str(exc))
