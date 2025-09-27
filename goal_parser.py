
from openai import OpenAI
import json
from datetime import datetime
from settings import load_settings

client = None

def ensure_client():
    global client
    cfg = load_settings()
    key = cfg.get("api_key", "")
    if not key:
        raise RuntimeError("OpenAI API key missing. Go to Settings and add your key.")
    client = OpenAI(api_key=key)
    return cfg

def get_local_start_time():
    return datetime.now().strftime("%H:%M")

def build_prompt(goals_text, context_text):
    local_start = get_local_start_time()
    return f"""{context_text}

Below are my daily goals:

{goals_text}

Create a JSON schedule starting at my current local time: {local_start}.
Use 3–4 blocks (BUILD, CREATE, CONNECT, MOVE). Include clear, short tasks.
Optimize for presence, health, and momentum.
Return ONLY valid JSON of the form:
{{
  "date": "YYYY-MM-DD",
  "timezone": "KST",
  "tasks": [{{"block":"BUILD","time":"15:00-17:00","tasks":["Task 1","Task 2"]}}]
}}
"""

def call_llm(prompt, model):
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert scheduler who outputs strict JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

def generate_schedule(goals_text, context_text):
    cfg = ensure_client()
    prompt = build_prompt(goals_text, context_text)
    raw = call_llm(prompt, model=cfg.get("model","gpt-4o-mini"))
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raw2 = raw.strip().strip("```").replace("json\n"," ").replace("JSON\n"," ")
        data = json.loads(raw2)
    with open("schedule.json","w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    stamp = datetime.now().strftime("%Y-%m-%d")
    with open(f"{stamp}_AI_Schedule.json","w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    return data
