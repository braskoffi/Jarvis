import os, tempfile
tmp=tempfile.NamedTemporaryFile(suffix=".db",delete=False);tmp.close()
os.environ["DATABASE_PATH"]=tmp.name
os.environ["APP_SECRET"]="test-secret-key-that-is-long-enough-123456"
os.environ["COOKIE_SECURE"]="0"
os.environ.pop("OPENAI_API_KEY",None)
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def test_health():
    r=client.get("/api/health")
    assert r.status_code==200 and r.json()["service"]=="JARVIS 2KR"

def test_register_and_me():
    r=client.post("/api/register",json={"email":"one@example.com","password":"correct-horse-battery"})
    assert r.status_code==200
    assert client.get("/api/me").status_code==200

def test_duplicate_email():
    client.post("/api/register",json={"email":"dup@example.com","password":"correct-horse-battery"})
    r=client.post("/api/register",json={"email":"dup@example.com","password":"correct-horse-battery"})
    assert r.status_code==409

def test_chat_requires_login():
    client.post("/api/logout")
    assert client.post("/api/chat",json={"message":"Bonjour"}).status_code==401

def test_memory_persists_without_key():
    client.post("/api/logout")
    client.post("/api/register",json={"email":"memory@example.com","password":"correct-horse-battery"})
    r=client.post("/api/chat",json={"message":"Mon projet test"})
    assert r.status_code==200
    history=client.get("/api/messages").json()["messages"]
    assert len(history)==2 and history[0]["content"]=="Mon projet test"

def test_sensitive_action_demo_only():
    client.post("/api/logout")
    client.post("/api/register",json={"email":"action@example.com","password":"correct-horse-battery"})
    p=client.post("/api/actions/propose",json={"action_type":"send_email","payload":{"description":"Demo"}})
    assert p.status_code==200 and p.json()["status"]=="pending"
    c=client.post("/api/actions/confirm",json={"action_id":p.json()["id"]})
    assert c.status_code==200 and "Aucun e-mail" in c.json()["message"]

def test_unknown_action_rejected():
    client.post("/api/logout")
    client.post("/api/register",json={"email":"unknown@example.com","password":"correct-horse-battery"})
    r=client.post("/api/actions/propose",json={"action_type":"shell_exec","payload":{"cmd":"whoami"}})
    assert r.status_code==400
