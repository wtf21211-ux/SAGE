from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel
import os
import json

# สร้างตัวแปร app ให้ตรงตามมาตรฐานที่ Vercel มองหา
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

@app.post("/api/generate-plan")
def generate_initial_plan(req: OnboardingRequest):
    current_time = get_thai_time()
    
    prompt = f"""
    คุณคือ "SAGE" นักวางแผนการเรียนเชิงจิตวิทยาสำหรับเด็กม.ปลาย
    เวลาไทยปัจจุบัน: {current_time}
    
    ข้อมูลนักเรียน:
    - ชื่อเล่น: {req.nickname}
    - เป้าหมายคณะ/มหาลัย: {req.target_uni}
    - MBTI: {req.mbti}
    - วิชาที่ถนัด/อ่อน: {req.strengths_weaknesses}
    - นิสัยการอ่านหนังสือ/เวลาว่าง: {req.study_style}

    จงวิเคราะห์จิตวิทยาการเรียนของเด็กคนนี้ และสร้างแผนการเรียน 2 ส่วน ตอบกลับเป็น JSON เท่านั้นตามโครงสร้างนี้:
    {{
        "psych_summary": "สรุปจุดเด่นและเทคนิคจิตวิทยาที่เหมาะกับ MBTI และนิสัยของเด็กคนนี้สั้นๆ 2-3 บรรทัด",
        "long_term_plan": "แผนการเตรียมตัวระยะยาวแบ่งเป็นเฟสๆ (เช่น เฟส 1 เก็บเนื้อหา, เฟส 2 ตะลุยโจทย์, เฟส 3 จับเวลาสอบ) จัดรูปแบบให้อ่านง่ายด้วย Markdown",
        "daily_tasks": [
            {{"id": 1, "task": "ชื่องานที่ต้องทำวันนี้ 1", "time": "45 นาที", "tip": "คำแนะนำตามสไตล์ MBTI", "done": false}},
            {{"id": 2, "task": "ชื่องานที่ต้องทำวันนี้ 2", "time": "30 นาที", "tip": "คำแนะนำตามสไตล์ MBTI", "done": false}},
            {{"id": 3, "task": "ชื่องานที่ต้องทำวันนี้ 3", "time": "20 นาที", "tip": "คำแนะนำตามสไตล์ MBTI", "done": false}}
        ]
    }}
    """

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "คุณตอบกลับเป็น JSON ที่ถูกต้องตามโครงสร้างที่กำหนดเท่านั้น ห้ามมีข้อความอื่นปน"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_with_sage(req: ChatRequest):
    current_time = get_thai_time()
    
    system_prompt = f"""
    คุณคือ "SAGE" (เซจ) AI ติวเตอร์ส่วนตัวและโค้ชจิตวิทยาสำหรับเด็กม.ปลาย
    - เวลาไทยปัจจุบัน: {current_time}
    - ข้อมูลโปรไฟล์นักเรียน: {req.profile_context}

    หน้าที่ของคุณ:
    1. ช่วยตอบคำถาม แก้ปัญหาการเรียน ปลอบใจเวลาท้อ หรือช่วยปรับแผนรายวันให้สอดคล้องกับเป้าหมายเข้ามหาลัย
    2. พูดคุยด้วยน้ำเสียงรุ่นพี่ที่ฉลาด สุขุม อบอุ่น เข้าใจธรรมชาติของ MBTI ของน้องคนนี้
    3. ดูเวลาไทยเสมอ หากดึกเกินไปให้เตือนพักผ่อน
    """

    try:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(req.history[-10:])
        messages.append({"role": "user", "content": req.message})

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return {"reply": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
