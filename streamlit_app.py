import streamlit as st
import pandas as pd
import datetime
import time
import random
from typing import List, Dict, Tuple
import re

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="EpidemicCare AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- THEME / CSS --------------------
st.markdown("""
<style>
/* gradient background for main block area only */
.block-container {
  padding-top: 1.5rem !important;
}
.ec-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 1.0rem 1.2rem;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
  margin-bottom: 1rem;
}
.ec-chip {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: #E8F4F8;
  color: #2E86AB;
  font-size: 0.85rem;
  margin-right: 0.5rem;
}
.ec-doctor {
  background: #E8F4F8;
  border-left: 6px solid #2E86AB;
  border-radius: 12px;
  padding: 0.9rem 1rem;
  margin-bottom: 0.6rem;
  font-size: 1.02rem;
}
.ec-user {
  background: #F0F7EE;
  border-left: 6px solid #3DAB6D;
  border-radius: 12px;
  padding: 0.9rem 1rem;
  margin-bottom: 0.6rem;
  font-size: 1.02rem;
}
.ec-title {
  color: #0074D9;
  margin: 0.25rem 0 0.6rem 0;
}
.ec-hero {
  text-align:center;
  padding: 1rem 0 0.5rem;
}
.ec-hero h1 {
  color:#0074D9; margin-bottom:0.25rem;
}
.ec-hero p { color:#0f172a; opacity:0.8; }
.ec-kicker { font-size:0.95rem; opacity:0.9; }
.stButton > button {
  background-color:#0074D9 !important; color:white !important;
  border:none; border-radius:10px; padding:0.55rem 1.0rem;
  transition: all .2s ease;
}
.stButton > button:hover { background-color:#005BB7 !important; }
.ec-reminder {
  background:#FFF4E5; border-left:4px solid #FFA500; border-radius:10px;
  padding:0.6rem 0.75rem; margin-bottom:0.6rem;
}
.small { font-size:0.9rem; opacity:0.85; }
.ec-footer { font-size:0.85rem; opacity:0.75; margin-top:0.75rem; }
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE --------------------
def ensure_state():
    ss = st.session_state
    ss.setdefault("page", "home")
    ss.setdefault("authenticated", True)  # keep simple; no backend auth
    ss.setdefault("user_data", {})
    ss.setdefault("symptoms", {})           # answers bucket
    ss.setdefault("chat_history", [])       # list[("doctor"|"user", text)]
    ss.setdefault("current_idx", 0)         # which question we are on
    ss.setdefault("treatment_plan", {})
    ss.setdefault("progress_data", {
        "start_date": None,
        "daily_rating": [],     # list of dicts {date, rating}
        "symptoms_track": [],   # list of dicts {date, symptoms: List[str]}
        "medication_taken": []  # list of dicts {date, taken: bool}
    })
    ss.setdefault("voice_enabled", True)     # browser speech on/off
    ss.setdefault("last_spoken_n", -1)       # to avoid repeat speech
ensure_state()

# -------------------- CONSULTATION STEPS --------------------
# Each step has: key, prompt, kind in {"text","number","choice"}, optional choices
STEPS: List[Dict] = [
    {"key":"name", "prompt":"What is your name?", "kind":"text"},
    {"key":"age", "prompt":"How old are you?", "kind":"number", "min":0, "max":120},
    {"key":"conditions", "prompt":"Do you have any pre-existing medical conditions? (optional)", "kind":"text"},
    {"key":"fever", "prompt":"Have you had a fever in the last 48 hours?", "kind":"choice", "choices":["Yes","No","Not sure"]},
    {"key":"cough_breathing", "prompt":"Any cough or difficulty breathing?", "kind":"choice", "choices":["Yes","No","Not sure"]},
    {"key":"body_aches", "prompt":"Any body aches or joint pain?", "kind":"choice", "choices":["Yes","No","Not sure"]},
    {"key":"loss_taste_smell", "prompt":"Have you noticed any loss of taste or smell?", "kind":"choice", "choices":["Yes","No","Not sure"]},
    {"key":"fatigue", "prompt":"Are you experiencing fatigue or unusual tiredness?", "kind":"choice", "choices":["Yes","No","Not sure"]},
    {"key":"other_symptoms", "prompt":"Any other symptoms you'd like to mention? (e.g., headache, rash, nausea)", "kind":"text"},
    {"key":"spo2", "prompt":"If you have a pulse oximeter, what is your oxygen saturation (SpO₂ %)? (optional)", "kind":"number", "min":70, "max":100}
]

# -------------------- DISEASE INFO --------------------
DISEASES = {
    "Influenza": {
        "symptom_keys": ["fever", "cough_breathing", "body_aches", "fatigue"],
        "keywords": ["sore throat", "chills", "body aches", "myalgia", "congestion"],
        "description": "A viral infection affecting the respiratory system.",
        "precautions": ["Rest", "Fluids", "Over-the-counter symptom relief as directed", "Consult a clinician if symptoms worsen"]
    },
    "COVID-19": {
        "symptom_keys": ["fever", "cough_breathing", "loss_taste_smell", "fatigue"],
        "keywords": ["sore throat", "congestion", "headache", "chills"],
        "description": "An infectious disease caused by SARS-CoV-2.",
        "precautions": ["Isolate when ill", "Rest and hydrate", "Consult a clinician", "Consider pulse-ox monitoring if available"]
    },
    "Dengue Fever": {
        "symptom_keys": ["fever", "body_aches", "fatigue"],
        "keywords": ["rash", "severe headache", "retro-orbital pain", "nausea", "vomiting"],
        "description": "A mosquito-borne viral illness common in tropical regions.",
        "precautions": ["Hydration", "Rest", "Avoid NSAIDs unless advised", "Seek medical care if bleeding or severe pain occurs"]
    },
    "Common Cold": {
        "symptom_keys": ["cough_breathing", "fatigue"],
        "keywords": ["runny nose", "sneezing", "congestion", "sore throat"],
        "description": "A mild viral infection of the upper respiratory tract.",
        "precautions": ["Rest", "Hydration", "Symptom relief as directed"]
    },
    "Mpox (Monkeypox)": {
        "symptom_keys": ["fever", "fatigue"],
        "keywords": ["rash", "lesions", "swollen lymph nodes", "lymphadenopathy", "chills"],
        "description": "A viral disease that can cause rash and systemic symptoms.",
        "precautions": ["Avoid close contact", "Cover lesions", "Consult a clinician", "Isolation until lesions crust and heal"]
    }
}

# -------------------- VOICE (BROWSER TTS) --------------------
def speak(text: str, autostart: bool = False, rate: float = 1.0, pitch: float = 1.0):
    """
    Uses the browser's Web Speech API. Works on most modern browsers.
    If autostart is True, it will speak immediately (may require user interaction).
    """
    safe = (text or "").replace("\\","\\\\").replace("`","\\`")
    auto_js = "true" if autostart else "false"
    st.components.v1.html(f"""
    <div>
      <button onclick="speakNow()" style="
        border:none;border-radius:10px;padding:6px 10px;margin:6px 0;
        background:#0074D9;color:white;cursor:pointer;">🔊 Speak</button>
    </div>
    <script>
      const txt = `{safe}`;
      function speakNow(){ 
        try {{
          const u = new SpeechSynthesisUtterance(txt);
          u.rate = {rate};
          u.pitch = {pitch};
          u.lang = 'en-US';
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(u);
        }} catch(e) {{ console.log(e); }}
      }
      if ({auto_js}) {{
        // attempt autoplay once
        setTimeout(() => {{
          try {{
            const u = new SpeechSynthesisUtterance(txt);
            u.rate = {rate};
            u.pitch = {pitch};
            u.lang = 'en-US';
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
          }} catch(e) {{}}
        }}, 100);
      }}
    </script>
    """, height=60)

# -------------------- CHAT HELPERS --------------------
def add_doctor(msg: str):
    st.session_state.chat_history.append(("doctor", msg))

def add_user(msg: str):
    st.session_state.chat_history.append(("user", msg))

def show_chat():
    for sender, message in st.session_state.chat_history[-250:]:
        if sender == "doctor":
            st.markdown(f'<div class="ec-doctor"><b>Dr. AI:</b> {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ec-user"><b>You:</b> {message}</div>', unsafe_allow_html=True)

# -------------------- RISK & DIAGNOSIS --------------------
def assess_risk(symptoms: Dict) -> Tuple[str, int, Dict]:
    score = 0
    detail = {}

    # Age
    age = symptoms.get("age")
    if isinstance(age, (int, float)):
        if age >= 60:
            score += 2; detail["age"] = 2
        elif age >= 40:
            score += 1; detail["age"] = 1
        else:
            detail["age"] = 0
    else:
        detail["age"] = 0

    # Pre-existing conditions
    if symptoms.get("conditions"):
        score += 2; detail["conditions"] = 2
    else:
        detail["conditions"] = 0

    # Binary symptoms (Yes/No/Not sure)
    weights = {
        "fever": 2,
        "cough_breathing": 3,
        "body_aches": 1,
        "loss_taste_smell": 2,
        "fatigue": 1
    }
    for k, w in weights.items():
        ans = symptoms.get(k)
        if ans == "Yes":
            score += w; detail[k] = w
        elif ans == "Not sure":
            score += max(1, int(round(w*0.5))); detail[k] = max(1, int(round(w*0.5)))
        else:
            detail[k] = 0

    # SpO2 weighting (optional)
    spo2 = symptoms.get("spo2")
    if isinstance(spo2, (int, float)):
        if spo2 < 90:
            score += 5; detail["spo2"] = 5
        elif spo2 < 94:
            score += 4; detail["spo2"] = 4
        elif spo2 < 96:
            score += 2; detail["spo2"] = 2
        else:
            detail["spo2"] = 0
    else:
        detail["spo2"] = 0

    # Risk level
    if score >= 9:
        level = "high"
    elif score >= 5:
        level = "medium"
    else:
        level = "low"

    return level, score, detail

def generate_diagnosis(symptoms: Dict) -> List[Tuple]:
    other = (symptoms.get("other_symptoms") or "").lower()
    possible = []
    for disease, info in DISEASES.items():
        matches = 0
        weight = 0
        # structured keys
        for k in info["symptom_keys"]:
            ans = symptoms.get(k)
            if ans == "Yes":
                matches += 1; weight += 2
            elif ans == "Not sure":
                matches += 0.5; weight += 1
        # keyword hits from free text
        kw_hits = 0
        for kw in info["keywords"]:
            if re.search(rf"\b{re.escape(kw)}\b", other):
                kw_hits += 1
        weight += kw_hits
        match_pct = min(100, int(round(100 * (matches / (len(info["symptom_keys"]) or 1)))))
        possible.append((
            disease,                       # 0
            match_pct,                     # 1
            info["description"],           # 2
            info["precautions"],           # 3
            weight                         # 4 (sort key)
        ))
    possible.sort(key=lambda x: x[4], reverse=True)
    return possible

def build_treatment_plan(risk: str, top_disease: str | None) -> Dict:
    plans = {
        "high": {
            "medication": [
                "Use over-the-counter symptom relief as directed (e.g., fever reducers).",
                "Only start antivirals/antibiotics if prescribed by a clinician."
            ],
            "rest": "Prioritize full rest and avoid exertion.",
            "diet": "2–3 liters fluids/day if not restricted; warm soups; balanced meals.",
            "monitoring": "Check temperature 2–4x/day. If available, monitor SpO₂. Watch for breathing difficulty, confusion, persistent chest pain.",
            "follow_up": "Seek medical advice within 24 hours or sooner if worsening.",
            "duration": "About 7–14 days depending on recovery.",
            "isolation": "Home isolation; mask around others; improve ventilation; separate utensils if feasible."
        },
        "medium": {
            "medication": [
                "Use OTC symptom relief as directed (e.g., acetaminophen for fever).",
                "Decongestants, throat lozenges may help."
            ],
            "rest": "Adequate rest; avoid strenuous activity.",
            "diet": "1.5–2 liters fluids/day; fruit/vegetable-rich diet; warm beverages.",
            "monitoring": "Check symptoms twice daily.",
            "follow_up": "Teleconsult in 48 hours or earlier if worsening.",
            "duration": "5–10 days.",
            "isolation": "Limit close contact; mask in shared spaces."
        },
        "low": {
            "medication": [
                "OTC remedies as needed and as directed.",
                "Saline nasal spray, honey-lemon for cough may provide comfort."
            ],
            "rest": "Resume light activities as tolerated; ensure good sleep.",
            "diet": "Normal diet with extra fluids.",
            "monitoring": "Observe for new or worsening symptoms.",
            "follow_up": "Consult if not improving after ~5 days.",
            "duration": "3–7 days.",
            "isolation": "Basic hygiene and courtesy masking if coughing/sneezing."
        }
    }
    plan = plans[risk].copy()

    # disease-specific flags
    if top_disease == "COVID-19":
        plan["monitoring"] += " Consider pulse-ox checks if available."
        plan["isolation"] = "Isolate at home; typical isolation ~10 days from symptom onset (follow local guidance)."
    elif top_disease == "Influenza":
        plan["medication"].insert(0, "Antivirals can help if started early — consult promptly.")
    elif top_disease == "Dengue Fever":
        plan["medication"].append("Avoid NSAIDs unless advised by a clinician.")
        plan["monitoring"] = "Hydrate well; seek care urgently for bleeding, severe abdominal pain, persistent vomiting, or drowsiness."
    elif top_disease == "Mpox (Monkeypox)":
        plan["isolation"] = "Avoid close contact; cover lesions; isolate until lesions crust/heal."

    return plan

# -------------------- PAGES --------------------
def page_home():
    st.markdown('<div class="ec-hero">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:3rem;line-height:1">🩺</div>', unsafe_allow_html=True)
    st.markdown('<h1>EpidemicCare AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="ec-kicker">Your intelligent assistant for epidemic symptom check, care guidance, and progress tracking.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2,1,1])
    with col1:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("How it works")
        st.markdown("- Answer a short consultation.\n- Review your risk & possible conditions.\n- Get a personalized care plan.\n- Track daily progress.")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Quick Tips")
        st.markdown("- Wash hands often.\n- Mask when ill or in crowds.\n- Stay hydrated.\n- Follow local health guidance.")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Get Started")
        st.markdown("Click below to begin your consultation.")
        if st.button("Start Consultation ➜"):
            st.session_state.page = "consult"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def page_consult():
    st.markdown('<h2 class="ec-title">EpidemicCare AI Doctor</h2>', unsafe_allow_html=True)

    # Sidebar actions
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.session_state.voice_enabled = st.toggle("Doctor voice", value=st.session_state.voice_enabled)
        st.caption("Uses your browser's speech synthesis.")
        st.markdown("---")
        if st.button("↻ Reset Conversation"):
            st.session_state.chat_history = []
            st.session_state.current_idx = 0
            st.session_state.symptoms = {}
            st.session_state.treatment_plan = {}
            st.session_state.progress_data = {"start_date": None, "daily_rating": [], "symptoms_track": [], "medication_taken": []}
            st.rerun()

    # Chat area
    with st.container():
        show_chat()

        # Ask current question
        idx = st.session_state.current_idx
        if idx < len(STEPS):
            step = STEPS[idx]
            prompt = step["prompt"]

            # Only add once per step
            if not st.session_state.chat_history or st.session_state.chat_history[-1][0] != "doctor" or st.session_state.chat_history[-1][1] != prompt:
                add_doctor(prompt)

            # Voice for the newest doctor message
            if st.session_state.voice_enabled and len(st.session_state.chat_history)-1 > st.session_state.last_spoken_n:
                speak(prompt, autostart=True)
                st.session_state.last_spoken_n = len(st.session_state.chat_history)-1

            # Input control
            st.markdown('<div class="ec-card">', unsafe_allow_html=True)
            if step["kind"] == "text":
                val = st.text_input("Your answer", key=f"in_{step['key']}", label_visibility="collapsed")
                if st.button("Submit", key=f"btn_{idx}"):
                    add_user(val if val else "(skipped)")
                    st.session_state.symptoms[step["key"]] = val.strip() if val else ""
                    st.session_state.current_idx += 1
                    st.rerun()

            elif step["kind"] == "number":
                minv = step.get("min", 0); maxv = step.get("max", 120)
                val = st.number_input("Your answer", min_value=minv, max_value=maxv, step=1, key=f"in_{step['key']}", label_visibility="collapsed")
                if st.button("Submit", key=f"btn_{idx}"):
                    add_user(str(val))
                    st.session_state.symptoms[step["key"]] = int(val)
                    st.session_state.current_idx += 1
                    st.rerun()

            elif step["kind"] == "choice":
                choices = step["choices"]
                val = st.radio("Choose one", choices, key=f"in_{step['key']}", label_visibility="collapsed")
                if st.button("Submit", key=f"btn_{idx}"):
                    add_user(val)
                    st.session_state.symptoms[step["key"]] = val
                    st.session_state.current_idx += 1
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Finish -> compute assessment
            add_doctor("Thanks. I'm analyzing your answers…")
            risk, score, detail = assess_risk(st.session_state.symptoms)
            possible = generate_diagnosis(st.session_state.symptoms)
            top = possible[0][0] if possible else None
            plan = build_treatment_plan(risk, top)
            st.session_state.treatment_plan = {
                "risk": risk, "score": score, "detail": detail, "possible": possible, "plan": plan
            }
            # init progress
            if not st.session_state.progress_data["start_date"]:
                st.session_state.progress_data["start_date"] = datetime.date.today()
            add_doctor("I've prepared a personalized care plan for you. You can review it under **Treatment Plan**.")
            if st.session_state.voice_enabled and len(st.session_state.chat_history)-1 > st.session_state.last_spoken_n:
                speak("I've prepared a personalized care plan for you. You can review it under Treatment Plan.", autostart=True)
                st.session_state.last_spoken_n = len(st.session_state.chat_history)-1

            colA, colB = st.columns([1,1])
            with colA:
                st.success(f"Risk Level: **{st.session_state.treatment_plan['risk'].upper()}**  | Score: {st.session_state.treatment_plan['score']}")
                if st.button("View Treatment Plan ➜"):
                    st.session_state.page = "plan"; st.rerun()
            with colB:
                st.info("Remember: This app provides educational guidance and is **not** a medical diagnosis. Seek professional care if you're concerned.")

def page_plan():
    st.markdown('<h2 class="ec-title">Your Treatment Plan</h2>', unsafe_allow_html=True)

    data = st.session_state.treatment_plan
    if not data:
        st.warning("Please complete the consultation first.")
        if st.button("Go to Consultation"):
            st.session_state.page = "consult"; st.rerun()
        return

    risk = data["risk"]; score = data["score"]; possible = data["possible"]; plan = data["plan"]

    col1, col2 = st.columns([1.1,1])
    with col1:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        if risk == "high":
            st.error(f"Risk Level: HIGH (score {score})")
        elif risk == "medium":
            st.warning(f"Risk Level: MEDIUM (score {score})")
        else:
            st.success(f"Risk Level: LOW (score {score})")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Possible Conditions")
        if possible:
            for disease, pct, desc, precautions, weight in possible[:3]:
                st.markdown(f"**{disease}** — approx. match: {pct}%")
                st.caption(desc)
                with st.expander("Recommended precautions"):
                    for p in precautions:
                        st.markdown(f"- {p}")
        else:
            st.info("Insufficient information to estimate conditions.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Care Guidance")
        st.markdown("**Medication / Symptom Relief**")
        for m in plan["medication"]:
            st.markdown(f"- {m}")
        st.markdown(f"**Rest:** {plan['rest']}")
        st.markdown(f"**Diet:** {plan['diet']}")
        st.markdown(f"**Monitoring:** {plan['monitoring']}")
        st.markdown(f"**Follow-up:** {plan['follow_up']}")
        st.markdown(f"**Expected Course:** {plan['duration']}")
        st.markdown(f"**Isolation / Precautions:** {plan['isolation']}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ec-card">', unsafe_allow_html=True)
    if st.button("Start Progress Tracking"):
        st.session_state.page = "progress"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def page_progress():
    st.markdown('<h2 class="ec-title">Your Progress Tracking</h2>', unsafe_allow_html=True)

    if not st.session_state.treatment_plan:
        st.warning("Complete the consultation to generate a plan before tracking progress.")
        if st.button("Go to Consultation"):
            st.session_state.page = "consult"; st.rerun()
        return

    col1, col2 = st.columns([1.05,0.95])
    with col1:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Daily Check-in")
        today = datetime.date.today()
        already = any(d["date"] == today for d in st.session_state.progress_data["daily_rating"])
        if not already:
            rating = st.slider("How are your symptoms today? (1 = very mild, 10 = very severe)", 1, 10, 5)
            sym = st.multiselect("Current symptoms",
                                 ["Fever","Cough","Headache","Fatigue","Body aches","Shortness of breath","Loss of taste/smell","Rash","Nausea/Vomiting"])
            taken = st.checkbox("I took my medicines as directed today")
            if st.button("Save Today's Progress"):
                st.session_state.progress_data["daily_rating"].append({"date": today, "rating": rating})
                st.session_state.progress_data["symptoms_track"].append({"date": today, "symptoms": sym})
                st.session_state.progress_data["medication_taken"].append({"date": today, "taken": bool(taken)})
                st.success("Saved!"); time.sleep(0.6); st.rerun()
        else:
            st.info("You've already checked in today. Come back tomorrow.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Symptom Severity Over Time")
        if st.session_state.progress_data["daily_rating"]:
            df = pd.DataFrame(st.session_state.progress_data["daily_rating"])
            df = df.sort_values("date")
            st.line_chart(df.set_index("date")["rating"])
        else:
            st.caption("No data yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Medication Adherence")
        med = st.session_state.progress_data["medication_taken"]
        if med:
            adherence = sum(1 for x in med if x["taken"])
            total = len(med)
            st.markdown(f"**Adherence:** {adherence}/{total} days ({(adherence/total)*100:.0f}%)")
            dfA = pd.DataFrame({"date":[x["date"] for x in med],
                                "adherence":[1 if x["taken"] else 0 for x in med]}).sort_values("date")
            st.bar_chart(dfA.set_index("date"))
        else:
            st.caption("No data yet.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Symptom Occurrence")
        hist = st.session_state.progress_data["symptoms_track"]
        if hist and any(x["symptoms"] for x in hist):
            rows = []
            for entry in hist:
                for s in entry["symptoms"]:
                    rows.append({"date": entry["date"], "symptom": s})
            dfS = pd.DataFrame(rows)
            pivot = pd.crosstab(dfS["date"], dfS["symptom"])
            st.bar_chart(pivot)
        else:
            st.caption("No symptom selections yet.")
        st.markdown('</div>', unsafe_allow_html=True)

def page_resources():
    st.markdown('<h2 class="ec-title">Health Resources</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Understanding Epidemic Illness")
        st.markdown("""
- **Early care matters:** rest, fluids, monitor warning signs.
- **Prevention:** hand hygiene, masking in crowds, ventilation, vaccinations per local guidance.
- **When to seek urgent care:** breathing trouble, SpO₂ < **94%** (if measured), chest pain, confusion, blue/gray lips or nailbeds, severe dehydration, persistent high fever.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Using a Pulse Oximeter (SpO₂)")
        st.markdown("""
1. Sit and rest your hand at heart level for 5 minutes.  
2. Remove nail polish or false nails.  
3. Clip the oximeter to your fingertip; keep still for ~30–60 seconds.  
4. Record the **highest stable** value.  
> Typical healthy readings are ~96–99% at sea level; trends over time matter.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("General Helplines")
        st.markdown("""
- **Emergency:** Use your local emergency number.  
- **Poison Help:** Local poison control center.  
- **Mental Health:** Local crisis hotline or text services in your country.
        """)
        st.caption("Numbers vary by country; check your local health authority website.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="ec-card">', unsafe_allow_html=True)
        st.subheader("Important Notes")
        st.markdown("""
- This app is for **education & guidance** only and does **not** replace professional medical advice, diagnosis, or treatment.  
- Always follow instructions from licensed healthcare professionals and local health authorities.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------- NAV / ROUTER --------------------
with st.sidebar:
    st.markdown("## 🩺 EpidemicCare AI")
    page = st.radio("Navigation", ["Home","Consultation","Treatment Plan","Progress","Resources"],
                    index=["home","consult","plan","progress","resources"].index(st.session_state.page)
                    if st.session_state.page in ["home","consult","plan","progress","resources"] else 0)
    if page == "Home": st.session_state.page = "home"
    elif page == "Consultation": st.session_state.page = "consult"
    elif page == "Treatment Plan": st.session_state.page = "plan"
    elif page == "Progress": st.session_state.page = "progress"
    else: st.session_state.page = "resources"

if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "consult":
    page_consult()
elif st.session_state.page == "plan":
    page_plan()
elif st.session_state.page == "progress":
    page_progress()
else:
    page_resources()

# -------------------- FOOTER --------------------
st.markdown('<div class="ec-footer">© 2025 EpidemicCare AI — Educational use only.</div>', unsafe_allow_html=True)
