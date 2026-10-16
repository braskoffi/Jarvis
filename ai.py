import os
from openai import OpenAI

SYSTEM_PROMPT = (
    "Tu es JARVIS 2KR, assistant personnel francophone au ton calme, précis et élégant, "
    "inspiré par les assistants high-tech de science-fiction. Ne prétends pas être le personnage du film "
    "ni être conscient. Sois honnête sur tes capacités. N'affirme jamais avoir effectué une tâche si aucun "
    "outil ne l'a fait. Les actions sensibles doivent demander confirmation explicite. Réponds en français."
)

def reply(messages):
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return "Mon interface fonctionne, mais l'IA en ligne n'est pas configurée. Ajoutez OPENAI_API_KEY dans .env puis redémarrez le serveur."
    try:
        client = OpenAI(api_key=key)
        safe = [{"role":"system","content":SYSTEM_PROMPT}]
        for m in messages[-20:]:
            if m.get("role") in ("user","assistant") and m.get("content"):
                safe.append({"role":m["role"],"content":str(m["content"])[:6000]})
        result = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"),
            messages=safe, temperature=0.6, max_tokens=900)
        return result.choices[0].message.content or "Je n'ai pas reçu de réponse exploitable."
    except Exception:
        return "Je rencontre un problème de connexion au service IA. Vérifiez la configuration du serveur et réessayez."
