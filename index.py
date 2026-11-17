from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from groq import Groq
from pydantic import BaseModel
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_thai_time():
    now_thai = datetime.now(ZoneInfo("Asia/Bangkok"))
    thai_days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    return f"วัน{thai_days[now_thai.weekday()]}ที่ {now_thai.strftime('%d/%m/%Y เวลา %H:%M น.')}"

class OnboardingRequest(BaseModel):
    nickname: str
    target_uni: str
    mbti: str
    strengths_weaknesses: str
    study_style: str

class ChatRequest(BaseModel):
    message: str
    profile_context: str = ""
    history: list = []

# เพิ่ม Route นี้เพื่อให้กดเข้าลิงก์ Render แล้วเปิดหน้า index.html ขึ้นมาโชว์ทันที
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>SAGE Backend is running! (ไม่พบไฟล์ index.html ในโฟลเดอร์หลัก)</h1>"

@app.post("/generate-plan")
def generate_initial_plan(req: OnboardingRequest):
    current_time = get_thai_time()
    prompt = f"""
    คุณคือ "SAGE" นักวางแผนการเรียนเชิงจิตวิทยาสำหรับเด็กม.ปลาย
    เวลาไทยปัจจุบัน: {current_time}
    ข้อมูลนักเรียน: ชื่อเล่น: {req.nickname}, เป้าหมาย: {req.target_uni}, MBTI: {req.mbti}, ถนัด/อ่อน: {req.strengths_weaknesses}, สไตล์: {req.study_style}
    ตอบกลับเป็น JSON เท่านั้น:
    {{"psych_summary": "สรุป...", "long_term_plan": "แผน...", "daily_tasks": [{{"id": 1, "task": "งาน", "time": "30 นาที", "tip": "ทริค", "done": false}}]}}
    """
    try:
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "system", "content": "ตอบเป็น JSON เท่านั้น"}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_with_sage(req: ChatRequest):
    current_time = get_thai_time()
    try:
        messages = [{"role": "system", "content": f"คุณคือ SAGE เวลา: {current_time} โปรไฟล์: {req.profile_context}"}]
        messages.extend(req.history[-10:])
        messages.append({"role": "user", "content": req.message})
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return {"reply": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# บรรทัดสั่งรัน Uvicorn สำหรับให้ Render เรียกใช้งาน
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
                                                                           
