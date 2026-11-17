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

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """<!DOCTYPE html>
<html lang="th" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAGE — AI Study & Mind Coach</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Prompt', sans-serif; background-color: #F8F9FA; color: #1E293B; }
        .luxury-card { background: #FFFFFF; border: 1px solid rgba(226, 232, 240, 0.8); box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.03); }
        .sage-logo-text { letter-spacing: 0.2em; font-weight: 600; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #E2E8F0; border-radius: 9999px; }
    </style>
</head>
<body class="h-full flex flex-col overflow-hidden">
    <header class="h-16 px-4 md:px-8 border-b border-slate-200/80 bg-white/90 backdrop-blur-md flex justify-between items-center shrink-0 z-10">
        <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-800">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
            </div>
            <div>
                <h1 class="text-sm md:text-base font-bold text-slate-900 sage-logo-text">SAGE</h1>
                <p class="text-[10px] text-slate-400 font-light -mt-0.5">Adaptive Study & Mind Coach</p>
            </div>
        </div>
        <div class="flex items-center gap-2 md:gap-3">
            <div class="text-xs px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200/60 text-slate-600 flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span id="time-text">--:--:--</span>
            </div>
            <button id="logout-btn" onclick="handleLogout()" class="hidden text-xs text-slate-500 hover:text-red-600 px-2.5 py-1.5 rounded-lg border border-slate-200 transition">ออก</button>
        </div>
    </header>

    <section id="auth-view" class="flex-1 flex items-center justify-center p-4 overflow-y-auto">
        <div class="luxury-card w-full max-w-md rounded-3xl p-6 md:p-8 space-y-6">
            <div class="text-center space-y-2">
                <h2 class="text-xl font-semibold text-slate-900">เข้าสู่ระบบ SAGE</h2>
                <p class="text-xs text-slate-400">วางแผนเตรียมสอบเข้ามหาลัยตามสไตล์จิตวิทยาของคุณ</p>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="text-xs text-slate-600 block mb-1">อีเมล</label>
                    <input type="email" id="auth-email" placeholder="student@example.com" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:border-blue-600">
                </div>
                <div>
                    <label class="text-xs text-slate-600 block mb-1">รหัสผ่าน</label>
                    <input type="password" id="auth-password" placeholder="••••••••" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:border-blue-600">
                </div>
                <p id="auth-error" class="text-xs text-red-500 hidden"></p>
                <div class="grid grid-cols-2 gap-3 pt-2">
                    <button onclick="handleAuth('login')" class="bg-blue-900 hover:bg-blue-800 text-white py-2.5 rounded-xl text-sm font-medium transition">เข้าสู่ระบบ</button>
                    <button onclick="handleAuth('signup')" class="bg-slate-100 hover:bg-slate-200 text-slate-800 py-2.5 rounded-xl text-sm font-medium transition">สมัครสมาชิก</button>
                </div>
            </div>
        </div>
    </section>

    <section id="onboarding-view" class="hidden flex-1 overflow-y-auto p-4 md:p-8">
        <div class="max-w-xl mx-auto luxury-card rounded-3xl p-6 md:p-8 space-y-5">
            <div>
                <span class="text-[11px] bg-blue-50 text-blue-700 px-3 py-1 rounded-full font-medium">ขั้นตอนตั้งค่าสมองกล AI</span>
                <h2 class="text-lg font-semibold text-slate-900 mt-2">มาทำความรู้จักสไตล์ของยูกันก่อน 📖</h2>
            </div>
            <div class="space-y-4 text-sm">
                <div>
                    <label class="text-xs font-medium text-slate-700 block mb-1">1. ชื่อเล่น & ชั้นปีปัจจุบัน</label>
                    <input type="text" id="ob-nickname" placeholder="เช่น มายด์ ม.5" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-xs md:text-sm focus:outline-none focus:border-blue-600">
                </div>
                <div>
                    <label class="text-xs font-medium text-slate-700 block mb-1">2. คณะและมหาวิทยาลัยที่อยากเข้า</label>
                    <input type="text" id="ob-target" placeholder="เช่น วิศวะคอม จุฬาฯ รอบ 3" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-xs md:text-sm focus:outline-none focus:border-blue-600">
                </div>
                <div>
                    <label class="text-xs font-medium text-slate-700 block mb-1">3. MBTI หรือนิสัยการทำงาน</label>
                    <input type="text" id="ob-mbti" placeholder="เช่น ENTP หรือ ชอบลุยเดี่ยว ขี้เบื่อง่าย" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-xs md:text-sm focus:outline-none focus:border-blue-600">
                </div>
                <div>
                    <label class="text-xs font-medium text-slate-700 block mb-1">4. วิชาที่ถนัด vs วิชาที่ไม่ชอบ</label>
                    <input type="text" id="ob-subjects" placeholder="เช่น ถนัดเลข แต่อ่อนชีวะ" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-xs md:text-sm focus:outline-none focus:border-blue-600">
                </div>
                <div>
                    <label class="text-xs font-medium text-slate-700 block mb-1">5. สไตล์การอ่านหนังสือ</label>
                    <textarea id="ob-style" rows="2" placeholder="เช่น ชอบอ่านตอนดึก พักทุก 45 นาที" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-xs md:text-sm focus:outline-none focus:border-blue-600"></textarea>
                </div>
                <button id="generate-btn" onclick="submitOnboarding()" class="w-full bg-blue-900 hover:bg-blue-800 text-white py-3 rounded-xl text-sm font-medium transition">✨ ให้ SAGE วิเคราะห์และสร้างแผนการเรียน</button>
            </div>
        </div>
    </section>

    <main id="dashboard-view" class="hidden flex-1 max-w-4xl w-full mx-auto flex flex-col overflow-hidden p-3 md:p-6">
        <nav class="grid grid-cols-3 gap-2 bg-slate-200/70 p-1.5 rounded-2xl mb-4 shrink-0">
            <button onclick="switchTab('daily')" id="tab-btn-daily" class="py-2 px-3 rounded-xl text-xs md:text-sm font-medium bg-white text-blue-900 shadow-xs transition">📌 แผนรายวัน</button>
            <button onclick="switchTab('longterm')" id="tab-btn-longterm" class="py-2 px-3 rounded-xl text-xs md:text-sm font-medium text-slate-600 hover:text-slate-900 transition">🗺️ แผนระยะยาว</button>
            <button onclick="switchTab('chat')" id="tab-btn-chat" class="py-2 px-3 rounded-xl text-xs md:text-sm font-medium text-slate-600 hover:text-slate-900 transition">💬 ปรึกษา AI</button>
        </nav>

        <section id="tab-daily" class="flex-1 luxury-card rounded-2xl flex flex-col overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-white">
                <div>
                    <h2 class="text-sm font-semibold text-slate-900">ภารกิจวันนี้ของ <span id="display-nickname" class="text-blue-800">คุณ</span></h2>
                    <p id="display-psych" class="text-[11px] text-slate-500 mt-0.5"></p>
                </div>
                <span id="task-progress" class="text-xs bg-blue-50 text-blue-700 px-3 py-1 rounded-full font-medium">0/0</span>
            </div>
            <div id="daily-tasks-list" class="flex-1 p-4 md:p-6 overflow-y-auto space-y-3 bg-[#F8F9FA]"></div>
        </section>

        <section id="tab-longterm" class="hidden flex-1 luxury-card rounded-2xl flex flex-col overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-white">
                <div>
                    <h2 class="text-sm font-semibold text-slate-900">เส้นทางสู่ <span id="display-target" class="text-blue-800">เป้าหมาย</span></h2>
                </div>
                <button onclick="resetOnboarding()" class="text-[11px] text-slate-500 underline">ตั้งค่าแผนใหม่</button>
            </div>
            <div id="long-term-content" class="flex-1 p-5 md:p-6 overflow-y-auto text-xs md:text-sm text-slate-700 leading-relaxed space-y-3 bg-[#F8F9FA]"></div>
        </section>

        <section id="tab-chat" class="hidden flex-1 luxury-card rounded-2xl flex flex-col overflow-hidden">
            <div class="px-5 py-3.5 border-b border-slate-100 bg-white flex justify-between items-center">
                <span class="text-xs md:text-sm font-medium text-slate-900">📖 ปรึกษาปัญหาการเรียน</span>
            </div>
            <div id="chat-box" class="flex-1 p-4 md:p-6 overflow-y-auto space-y-4 text-xs md:text-sm bg-[#F8F9FA]">
                <div class="flex items-start gap-3">
                    <div class="w-7 h-7 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center shrink-0 text-xs font-bold">S</div>
                    <div class="bg-white border border-slate-200/60 text-slate-700 p-3.5 rounded-2xl rounded-tl-none max-w-[85%] shadow-xs">มีตรงไหนอ่านไม่เข้าใจ ท้อ หรืออยากปรับตารางวันนี้ไหม? บอกพี่ได้เลย!</div>
                </div>
            </div>
            <div class="p-3 border-t border-slate-100 bg-white">
                <div class="flex items-center gap-2 bg-[#F8F9FA] border border-slate-200 rounded-xl px-3 py-1.5">
                    <input type="text" id="user-input" placeholder="พิมพ์คุยกับ AI..." class="flex-1 bg-transparent py-1.5 text-xs md:text-sm focus:outline-none">
                    <button onclick="sendMessage()" class="bg-blue-900 text-white px-4 py-2 rounded-lg text-xs font-medium">ส่ง</button>
                </div>
            </div>
        </section>
    </main>

    <script>
        (function() {
            function updateThaiTime() {
                const timeEl = document.getElementById('time-text');
                if (timeEl) {
                    timeEl.innerText = new Date().toLocaleTimeString("th-TH", { timeZone: "Asia/Bangkok", hour: '2-digit', minute: '2-digit', second: '2-digit' });
                }
            }
            updateThaiTime();
            setInterval(updateThaiTime, 1000);
        })();

        const SUPABASE_URL = 'https://ejfaubbngflxprhgvrlg.supabase.co';
        const SUPABASE_ANON_KEY = 'sb_publishable_T1UXpP2GYNYGWSm8hM6XCg_3rqtIx21';
        const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

        let currentUser = null;
        let userPlanData = null;
        let chatHistory = [];

        async function checkSession() {
            const { data: { session } } = await supabaseClient.auth.getSession();
            if (session) {
                currentUser = session.user;
                document.getElementById('logout-btn').classList.remove('hidden');
                loadUserPlan();
            } else {
                showView('auth-view');
            }
        }
        checkSession();

        function showView(viewId) {
            ['auth-view', 'onboarding-view', 'dashboard-view'].forEach(id => {
                const el = document.getElementById(id);
                if(el) el.classList.add('hidden');
            });
            const target = document.getElementById(viewId);
            if(target) target.classList.remove('hidden');
        }

        async function handleAuth(type) {
            const email = document.getElementById('auth-email').value;
            const password = document.getElementById('auth-password').value;
            const errEl = document.getElementById('auth-error');
            errEl.classList.add('hidden');

            let res = type === 'login' 
                ? await supabaseClient.auth.signInWithPassword({ email, password })
                : await supabaseClient.auth.signUp({ email, password });

            if (res.error) {
                errEl.innerText = res.error.message;
                errEl.classList.remove('hidden');
            } else {
                currentUser = res.data.user;
                document.getElementById('logout-btn').classList.remove('hidden');
                loadUserPlan();
            }
        }

        async function handleLogout() {
            await supabaseClient.auth.signOut();
            location.reload();
        }

        async function loadUserPlan() {
            const { data } = await supabaseClient.from('user_plans').select('*').eq('user_id', currentUser.id).single();
            if (data && data.long_term_plan) {
                userPlanData = data;
                renderDashboard();
                showView('dashboard-view');
            } else {
                showView('onboarding-view');
            }
        }

        async function submitOnboarding() {
            const btn = document.getElementById('generate-btn');
            btn.innerText = "⏳ SAGE กำลังวิเคราะห์และจัดตาราง...";
            btn.disabled = true;

            const payload = {
                nickname: document.getElementById('ob-nickname').value,
                target_uni: document.getElementById('ob-target').value,
                mbti: document.getElementById('ob-mbti').value,
                strengths_weaknesses: document.getElementById('ob-subjects').value,
                study_style: document.getElementById('ob-style').value
            };

            try {
                const fetchRes = await fetch('/generate-plan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const aiData = await fetchRes.json();

                if (!fetchRes.ok) throw new Error(aiData.detail || "เกิดข้อผิดพลาด");

                const newPlan = {
                    user_id: currentUser.id,
                    nickname: payload.nickname,
                    target_uni: payload.target_uni,
                    mbti: payload.mbti,
                    psych_summary: aiData.psych_summary,
                    long_term_plan: aiData.long_term_plan,
                    daily_tasks: aiData.daily_tasks
                };

                await supabaseClient.from('user_plans').upsert(newPlan);
                userPlanData = newPlan;
                renderDashboard();
                showView('dashboard-view');
            } catch (err) {
                alert("เกิดข้อผิดพลาด: " + err.message);
            } finally {
                btn.innerText = "✨ ให้ SAGE วิเคราะห์และสร้างแผนการเรียน";
                btn.disabled = false;
            }
        }

        function resetOnboarding() { showView('onboarding-view'); }

        function renderDashboard() {
            document.getElementById('display-nickname').innerText = userPlanData.nickname || 'คุณ';
            document.getElementById('display-psych').innerText = userPlanData.psych_summary || '';
            document.getElementById('display-target').innerText = userPlanData.target_uni || 'เป้าหมาย';
            document.getElementById('long-term-content').innerHTML = userPlanData.long_term_plan.replace(/\\*\\*(.*?)\\*\\*/g, '<b class="text-slate-900">$1</b>').replace(/\\n/g, '<br>');
            renderTasks();
        }

        function renderTasks() {
            const listEl = document.getElementById('daily-tasks-list');
            const tasks = userPlanData.daily_tasks || [];
            listEl.innerHTML = '';
            tasks.forEach((t, idx) => {
                listEl.innerHTML += `
                    <label class="flex items-start gap-3 p-4 bg-white border border-slate-200/80 rounded-xl cursor-pointer shadow-xs">
                        <input type="checkbox" ${t.done ? 'checked' : ''} onchange="toggleTask(${idx})" class="mt-1 w-4 h-4 accent-blue-900">
                        <div class="flex-1">
                            <p class="font-medium text-xs md:text-sm ${t.done ? 'line-through text-slate-400' : 'text-slate-800'}">${t.task}</p>
                            <p class="text-[11px] text-slate-400 mt-1">⏱️ ${t.time} • <span class="text-blue-700">${t.tip}</span></p>
                        </div>
                    </label>
                `;
            });
            document.getElementById('task-progress').innerText = `${tasks.filter(t => t.done).length}/${tasks.length} สำเร็จ`;
        }

        async function toggleTask(index) {
            userPlanData.daily_tasks[index].done = !userPlanData.daily_tasks[index].done;
            renderTasks();
            await supabaseClient.from('user_plans').update({ daily_tasks: userPlanData.daily_tasks }).eq('user_id', currentUser.id);
        }

        function switchTab(tabName) {
            ['daily', 'longterm', 'chat'].forEach(name => {
                document.getElementById(`tab-${name}`).classList.add('hidden');
                document.getElementById(`tab-btn-${name}`).className = "py-2 px-3 rounded-xl text-xs md:text-sm font-medium text-slate-600 hover:text-slate-900 transition";
            });
            document.getElementById(`tab-${tabName}`).classList.remove('hidden');
            document.getElementById(`tab-btn-${tabName}`).className = "py-2 px-3 rounded-xl text-xs md:text-sm font-medium bg-white text-blue-900 shadow-xs transition";
        }

        async function sendMessage() {
            const input = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');
            const text = input.value.trim();
            if (!text) return;

            chatBox.innerHTML += `<div class="flex justify-end"><div class="bg-blue-900 text-white p-3.5 rounded-2xl rounded-tr-none max-w-[85%]">${text}</div></div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const profileContext = `ชื่อ: ${userPlanData.nickname}, เป้าหมาย: ${userPlanData.target_uni}, MBTI: ${userPlanData.mbti}`;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, profile_context: profileContext, history: chatHistory })
                });
                const data = await res.json();
                chatHistory.push({ role: 'user', content: text }, { role: 'assistant', content: data.reply });

                const formatted = data.reply.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>').replace(/\\n/g, '<br>');
                chatBox.innerHTML += `<div class="flex items-start gap-2.5"><div class="w-7 h-7 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center shrink-0 text-xs font-bold">S</div><div class="bg-white border border-slate-200/60 p-3.5 rounded-2xl rounded-tl-none max-w-[85%] shadow-xs">${formatted}</div></div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            } catch (e) {
                alert("ส่งข้อความไม่สำเร็จ");
            }
        }
    </script>
</body>
</html>
"""

@app.post("/generate-plan")
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
        "long_term_plan": "แผนการเตรียมตัวระยะยาวแบ่งเป็นเฟสๆ จัดรูปแบบให้อ่านง่ายด้วย Markdown",
        "daily_tasks": [
            {{"id": 1, "task": "ชื่องานที่ต้องทำวันนี้ 1", "time": "45 นาที", "tip": "คำแนะนำตามสไตล์ MBTI", "done": false}},
            {{"id": 2, "task": "ชื่องานที่ต้องทำวันนี้ 2", "time": "30 นาที", "tip": "คำแนะนำตามสไตล์ MBTI", "done": false}},
            {{"id": 3, "task": "ชื่องานที่ต้องทำวันนี้ 3", "time": "20 นาที", "tip": "คำแนะนำตามสไตล์ MBTI", "done": false}}
        ]
    }}
    """
    try:
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
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

@app.post("/chat")
def chat_with_sage(req: ChatRequest):
    current_time = get_thai_time()
    system_prompt = f"""
    คุณคือ "SAGE" (เซจ) AI ติวเตอร์ส่วนตัวและโค้ชจิตวิทยาสำหรับเด็กม.ปลาย
    - เวลาไทยปัจจุบัน: {current_time}
    - ข้อมูลโปรไฟล์นักเรียน: {req.profile_context}
    """
    try:
        messages = [{"role": "system", "content": system_prompt}]
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
