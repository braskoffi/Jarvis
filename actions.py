import json, uuid
from . import database

ALLOWED = {"create_reminder", "send_email", "delete_file", "run_program"}

def propose(uid, kind, payload):
    if kind not in ALLOWED:
        raise ValueError("Type d'action inconnu.")
    aid = uuid.uuid4().hex
    database.add_action(aid, uid, kind, json.dumps(payload, ensure_ascii=False))
    return {"id":aid,"type":kind,"payload":payload,"status":"pending",
            "message":"Action préparée. Aucune action réelle n'a été exécutée."}

def confirm(uid, aid):
    item = database.pending_action(aid, uid)
    if not item: raise ValueError("Action introuvable, déjà traitée ou non autorisée.")
    database.finish_action(aid, uid)
    return {"id":aid,"status":"confirmed_demo",
            "message":"Confirmation enregistrée en mode démonstration. Aucun e-mail, fichier ou programme n'a été modifié."}
