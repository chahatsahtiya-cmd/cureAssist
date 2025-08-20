import streamlit as st
import pandas as pd
import datetime
import time
import random

# Page configuration
st.set_page_config(
    page_title="EpidemicCare AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0074D9 0%, #2E86AB 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
    }
    .blue-bg {
        background-color: #0074D9;
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1.5rem;
    }
    .doctor-chat {
        background-color: #E8F4F8;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        border-left: 5px solid #2E86AB;
        font-size: 1.1rem;
    }
    .user-chat {
        background-color: #F0F7EE;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        border-left: 5px solid #3DAB6D;
        font-size: 1.1rem;
    }
    .stButton>button {
        background-color: #0074D9;
        color: white;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 8px;
        font-size: 1rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #005BB7;
        color: white;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    .progress-bar {
        height: 1.5rem;
        background-color: #E0E0E0;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .progress-fill {
        height: 100%;
        background-color: #0074D9;
        border-radius: 10px;
        text-align: center;
        color: white;
        line-height: 1.5rem;
    }
    .reminder-card {
        background-color: #FFF4E5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #FFA500;
        margin-bottom: 1rem;
    }
    .feature-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        text-align: center;
        transition: transform 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .symptom-item {
        padding: 0.5rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        background-color: #F0F8FF;
    }
    .logo-container {
        text-align: center;
        margin-bottom: 2rem;
    }
    .logo {
        font-size: 4rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "welcome"
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'symptoms' not in st.session_state:
    st.session_state.symptoms = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'treatment_plan' not in st.session_state:
    st.session_state.treatment_plan = {}
if 'progress_data' not in st.session_state:
    st.session_state.progress_data = {}

# Disease database with more details
diseases = {
    "Influenza": {
        "symptoms": ["fever", "cough", "sore throat", "body aches", "fatigue", "headache", "chills"],
        "description": "A viral infection that attacks your respiratory system.",
        "precautions": ["Rest", "Hydration", "Over-the-counter fever reducers", "Antiviral medications if prescribed"],
        "contagious_period": "1 day before to 5-7 days after symptoms appear",
        "recovery_time": "3-7 days for most people"
    },
    "COVID-19": {
        "symptoms": ["fever", "cough", "shortness of breath", "loss of taste", "loss of smell", "fatigue", "body aches", "headache"],
        "description": "A contagious disease caused by the SARS-CoV-2 virus.",
        "precautions": ["Isolation", "Rest", "Medical consultation", "Symptom monitoring", "Oxygen monitoring if severe"],
        "contagious_period": "2 days before symptoms to 10 days after",
        "recovery_time": "2-6 weeks depending on severity"
    },
    "Dengue Fever": {
        "symptoms": ["high fever", "severe headache", "pain behind eyes", "joint pain", "rash", "nausea", "vomiting"],
        "description": "A mosquito-borne tropical disease caused by the dengue virus.",
        "precautions": ["Hydration", "Rest", "Medical supervision", "Mosquito protection", "Avoid aspirin"],
        "contagious_period": "Not directly contagious from person to person",
        "recovery_time": "2-7 days for acute phase, weeks for full recovery"
    },
    "Common Cold": {
        "symptoms": ["runny nose", "sneezing", "congestion", "mild cough", "sore throat", "mild headache"],
        "description": "A viral infection of your nose and throat.",
        "precautions": ["Rest", "Hydration", "Over-the-counter cold medicine", "Steam inhalation"],
        "contagious_period": "1-2 days before symptoms to 5-7 days after",
        "recovery_time": "7-10 days"
    },
    "Monkeypox": {
        "symptoms": ["fever", "headache", "muscle aches", "swollen lymph nodes", "rash", "chills", "exhaustion"],
        "description": "A viral disease that causes pox-like skin lesions.",
        "precautions": ["Isolation", "Symptomatic treatment", "Vaccination if available", "Avoid scratching lesions"],
        "contagious_period": "From symptom onset until lesions have crusted over",
        "recovery_time": "2-4 weeks"
    }
}

# Advanced AI doctor responses
def get_ai_response(step, user_input=None):
    responses = {
        0: "Hello! I'm Dr. AI, your medical assistant. What's your name?",
        1: f"Nice to meet you, {user_input}! How old are you?",
        2: "Do you have any pre-existing medical conditions?",
        3: "Let's talk about your symptoms. Have you had a fever in the last 48 hours?",
        4: "Are you experiencing any cough or difficulty breathing?",
        5: "Do you have any body aches or joint pain?",
        6: "Have you noticed any loss of taste or smell?",
        7: "Are you experiencing fatigue or unusual tiredness?",
        8: "Any other symptoms you'd like to mention?",
        9: "Thank you. I'm now analyzing your symptoms...",
        10: "Based on your symptoms, I'm developing a personalized treatment plan for you.",
        11: "I've prepared a comprehensive treatment plan. Let me walk you through it."
    }
    
    # Add some variability to responses
    variations = {
        1: [f"Hello {user_input}! I'm Dr. AI. How old are you?", f"Pleased to meet you, {user_input}. What's your age?"],
        3: ["Let's discuss your symptoms. Have you had a fever recently?", "To better understand your condition, have you experienced fever in the last 2 days?"],
        9: ["Thank you for that information. I'm processing your symptoms now...", "I appreciate you sharing these details. I'm analyzing your symptoms..."]
    }
    
    if step in variations:
        return random.choice(variations[step])
    return responses.get(step, "I'm here to help. Please tell me more about your symptoms.")

# Function to navigate between pages
def navigate_to(page):
    st.session_state.page = page

# Function to display welcome page
def show_welcome():
    st.markdown("""
    <div class="logo-container">
        <div class="logo">🩺</div>
        <h1 style="color: #0074D9;">EpidemicCare AI</h1>
        <p>Your intelligent health assistant for epidemic diseases</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <h2 style="color: #0074D9;">Welcome to EpidemicCare AI</h2>
            <p>Your personal AI doctor for epidemic disease assessment and management</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.image("https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80", 
                 use_column_width=True, caption="AI-Powered Healthcare")
        
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h3>How it works:</h3>
            <p>1. Sign up for an account</p>
            <p>2. Consult with our AI doctor</p>
            <p>3. Receive a personalized treatment plan</p>
            <p>4. Track your daily progress</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Get Started", key="welcome_btn", use_container_width=True):
            navigate_to("auth")
            st.experimental_rerun()

# Function to display authentication UI
def show_auth_ui():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="logo-container">
            <div class="logo">🩺</div>
            <h2 style="color: #0074D9;">EpidemicCare AI</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="blue-bg">
            <h3 style="text-align: center; color: white;">Create Account or Sign In</h3>
        </div>
        """, unsafe_allow_html=True)
        
        auth_tab, register_tab = st.tabs(["Login", "Create Account"])
        
        with auth_tab:
            st.subheader("Login to Your Account")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_btn", use_container_width=True):
                if email and password:
                    st.session_state.authenticated = True
                    st.session_state.user_data = {"email": email}
                    st.success("Login successful!")
                    time.sleep(1)
                    navigate_to("consultation")
                    st.experimental_rerun()
                else:
                    st.error("Please enter both email and password")
        
        with register_tab:
            st.subheader("Create New Account")
            new_name = st.text_input("Full Name", key="reg_name")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            if st.button("Create Account", key="reg_btn", use_container_width=True):
                if new_name and new_email and new_password:
                    if new_password == confirm_password:
                        st.session_state.authenticated = True
                        st.session_state.user_data = {
                            "name": new_name,
                            "email": new_email
                        }
                        st.success("Account created successfully!")
                        time.sleep(1)
                        navigate_to("consultation")
                        st.experimental_rerun()
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill all fields")

# Function to display chat message
def display_chat():
    for sender, message in st.session_state.chat_history:
        if sender == "doctor":
            st.markdown(f'<div class="doctor-chat"><b>Dr. AI:</b> {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="user-chat"><b>You:</b> {message}</div>', unsafe_allow_html=True)

# Function to assess risk with more advanced algorithm
def assess_risk():
    symptoms_list = []
    symptom_severity = {
        "fever": 2,
        "high fever": 3,
        "cough": 1,
        "difficulty breathing": 3,
        "shortness of breath": 3,
        "body aches": 1,
        "joint pain": 1,
        "loss of taste": 2,
        "loss of smell": 2,
        "fatigue": 1,
        "severe headache": 2,
        "rash": 1,
        "nausea": 1,
        "vomiting": 2,
        "chills": 1,
        "swollen lymph nodes": 2
    }
    
    risk_score = 0
    age = st.session_state.symptoms.get('age', 30)
    
    # Age factor (older patients at higher risk)
    if age > 60:
        risk_score += 2
    elif age > 40:
        risk_score += 1
    
    # Check for key symptoms
    for key, value in st.session_state.symptoms.items():
        if key.startswith('symptom_') and value in ["Yes", True]:
            symptom_name = key.replace('symptom_', '').replace('_', ' ')
            symptoms_list.append(symptom_name)
            risk_score += symptom_severity.get(symptom_name, 1)
    
    # Pre-existing conditions increase risk
    if st.session_state.symptoms.get('conditions'):
        risk_score += 2
    
    # Determine risk level
    if risk_score >= 8:
        return "high", risk_score
    elif risk_score >= 5:
        return "medium", risk_score
    else:
        return "low", risk_score

# Function to generate diagnosis with more advanced matching
def generate_diagnosis():
    user_symptoms = []
    for key, value in st.session_state.symptoms.items():
        if key.startswith('symptom_') and value in ["Yes", True]:
            symptom_name = key.replace('symptom_', '').replace('_', ' ')
            user_symptoms.append(symptom_name)
    
    possible_diseases = []
    for disease, info in diseases.items():
        match_count = 0
        symptom_weight = 0
        
        for symptom in user_symptoms:
            if symptom in info["symptoms"]:
                match_count += 1
                # Weight more specific symptoms higher
                if symptom in ["loss of taste", "loss of smell", "swollen lymph nodes"]:
                    symptom_weight += 2
                else:
                    symptom_weight += 1
        
        if match_count > 0:
            match_percentage = (match_count / len(info["symptoms"])) * 100
            # Adjust score based on symptom weight
            weighted_score = match_count + (symptom_weight * 0.5)
            possible_diseases.append((disease, match_count, info["description"], match_percentage, info["precautions"], weighted_score, info["contagious_period"], info["recovery_time"]))
    
    # Sort by weighted score (descending)
    possible_diseases.sort(key=lambda x: x[5], reverse=True)
    
    return possible_diseases

# Function to generate more detailed treatment plan
def generate_treatment_plan(risk_level, possible_diseases):
    plans = {
        "high": {
            "medication": ["Antiviral medication (if prescribed)", "Paracetamol for fever (500mg every 6 hours)", "Cough syrup (as needed)", "Vitamin C supplements"],
            "rest": "Complete bed rest for at least 5-7 days. Avoid any physical exertion.",
            "diet": "Plenty of fluids (2-3 liters daily), light meals, vitamin C rich foods (citrus fruits, berries), easily digestible proteins",
            "monitoring": "Check temperature every 4 hours, monitor oxygen levels (if oximeter available), watch for breathing difficulties",
            "follow_up": "Teleconsultation within 24 hours. Visit emergency if oxygen saturation drops below 94% or breathing becomes difficult.",
            "duration": "7-14 days depending on recovery",
            "isolation": "Strict isolation recommended. Use separate bathroom if possible. Wear mask around others."
        },
        "medium": {
            "medication": ["Paracetamol as needed for fever", "Decongestants if required", "Throat lozenges for cough", "Multivitamins"],
            "rest": "Adequate rest, avoid strenuous activities. 7-8 hours of sleep nightly.",
            "diet": "Increased fluid intake (1.5-2 liters daily), balanced diet with fruits and vegetables, warm soups",
            "monitoring": "Check temperature twice daily. Watch for new or worsening symptoms.",
            "follow_up": "Teleconsultation in 48 hours. Seek in-person care if symptoms worsen.",
            "duration": "5-10 days",
            "isolation": "Home isolation advised. Maintain distance from household members."
        },
        "low": {
            "medication": ["Over-the-counter symptom relief as needed", "Saline nasal spray for congestion", "Honey and lemon for cough"],
            "rest": "Normal activities with adequate sleep. Listen to your body and rest when tired.",
            "diet": "Normal healthy diet with extra fluids. Herbal teas may provide comfort.",
            "monitoring": "Watch for new or worsening symptoms. Temperature check once daily.",
            "follow_up": "Consult if symptoms persist beyond 5 days or worsen.",
            "duration": "3-7 days",
            "isolation": "Precautionary measures recommended. Good hygiene practices."
        }
    }
    
    base_plan = plans[risk_level]
    
    # Customize based on likely diseases
    if possible_diseases:
        top_disease = possible_diseases[0][0]
        if top_disease == "COVID-19":
            base_plan["medication"].append("Consider pulse oximetry monitoring")
            base_plan["isolation"] = "Strict isolation for 10 days from symptom onset"
        elif top_disease == "Influenza":
            base_plan["medication"].append("Antiviral medication may be beneficial if started early")
        elif top_disease == "Dengue Fever":
            base_plan["medication"].append("Avoid NSAIDs like ibuprofen or aspirin")
            base_plan["monitoring"] = "Watch for warning signs like severe abdominal pain, bleeding, or drowsiness"
    
    return base_plan

# Function to show AI doctor interface
def show_ai_doctor():
    st.markdown("""
    <div class="logo-container">
        <div class="logo">🩺</div>
        <h2 style="color: #0074D9;">EpidemicCare AI Doctor</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Consultation Chat")
        display_chat()
        
        if st.session_state.current_step < len(questions):
            current_question = get_ai_response(st.session_state.current_step, st.session_state.symptoms.get('name'))
            
            if not st.session_state.chat_history or st.session_state.chat_history[-1][1] != current_question:
                st.session_state.chat_history.append(("doctor", current_question))
            
            if st.session_state.current_step == 0:
                name = st.text_input("Your answer:", key="input_0", label_visibility="collapsed")
                if st.button("Submit", key="button_0"):
                    if name:
                        st.session_state.symptoms['name'] = name
                        st.session_state.chat_history.append(("user", name))
                        st.session_state.current_step += 1
                        st.experimental_rerun()
            
            elif st.session_state.current_step == 1:
                age = st.number_input("Your answer:", min_value=0, max_value=120, key="input_1", label_visibility="collapsed")
                if st.button("Submit", key="button_1"):
                    st.session_state.symptoms['age'] = age
                    st.session_state.chat_history.append(("user", str(age)))
                    st.session_state.current_step += 1
                    st.experimental_rerun()
            
            elif st.session_state.current_step == 2:
                conditions = st.text_input("Your answer:", key="input_2", label_visibility="collapsed")
                if st.button("Submit", key="button_2"):
                    st.session_state.symptoms['conditions'] = conditions
                    st.session_state.chat_history.append(("user", conditions if conditions else "None"))
                    st.session_state.current_step += 1
                    st.experimental_rerun()
            
            else:
                options = ["Yes", "No", "Not sure"]
                response = st.radio("Your answer:", options, key=f"input_{st.session_state.current_step}", label_visibility="collapsed")
                if st.button("Submit", key=f"button_{st.session_state.current_step}"):
                    st.session_state.symptoms[f'symptom_{st.session_state.current_step}'] = response
                    st.session_state.chat_history.append(("user", response))
                    
                    if st.session_state.current_step == len(questions) - 1:
                        # Add analyzing message
                        st.session_state.chat_history.append(("doctor", get_ai_response(9)))
                        st.session_state.chat_history.append(("doctor", get_ai_response(10)))
                        st.session_state.current_step += 1
                    else:
                        st.session_state.current_step += 1
                    
                    st.experimental_rerun()
        
        elif st.session_state.current_step == len(questions):
            # Generate assessment
            risk_level, risk_score = assess_risk()
            possible_diseases = generate_diagnosis()
            st.session_state.treatment_plan = generate_treatment_plan(risk_level, possible_diseases)
            
            # Initialize progress tracking
            st.session_state.progress_data = {
                "start_date": datetime.date.today(),
                "symptoms_track": [],
                "medication_taken": [],
                "daily_rating": []
            }
            
            st.session_state.chat_history.append(("doctor", get_ai_response(11)))
            st.session_state.current_step += 1
            st.experimental_rerun()
        
        else:
            # Show assessment results
            risk_level, risk_score = assess_risk()
            possible_diseases = generate_diagnosis()
            
            st.markdown("### Assessment Results")
            
            if risk_level == "high":
                st.error(f"Risk Level: HIGH ({risk_score}/15 points)")
                st.warning("Based on your symptoms, you may be at high risk. Please consult a healthcare professional immediately.")
            elif risk_level == "medium":
                st.warning(f"Risk Level: MEDIUM ({risk_score}/15 points)")
                st.info("Your symptoms suggest moderate risk. Monitor your condition and consider consulting a doctor if symptoms persist.")
            else:
                st.success(f"Risk Level: LOW ({risk_score}/15 points)")
                st.info("Your symptoms suggest low risk. Continue to practice good hygiene and monitor your health.")
            
            if possible_diseases:
                st.markdown("### Possible Conditions")
                for disease, match_count, description, match_percentage, precautions, weighted_score, contagious_period, recovery_time in possible_diseases[:2]:
                    st.markdown(f"**{disease}** ({match_percentage:.0f}% match)")
                    st.caption(description)
                    with st.expander("More details"):
                        st.markdown(f"**Contagious Period:** {contagious_period}")
                        st.markdown(f"**Typical Recovery Time:** {recovery_time}")
                        st.markdown("**Recommended Precautions:**")
                        for precaution in precautions:
                            st.markdown(f"- {precaution}")
            
            st.markdown("### Your Personalized Treatment Plan")
            plan = st.session_state.treatment_plan
            
            with st.expander("View Detailed Treatment Plan"):
                st.markdown("**Medication:**")
                for med in plan["medication"]:
                    st.markdown(f"- {med}")
                
                st.markdown(f"**Rest:** {plan['rest']}")
                st.markdown(f"**Diet:** {plan['diet']}")
                st.markdown(f"**Monitoring:** {plan['monitoring']}")
                st.markdown(f"**Follow-up:** {plan['follow_up']}")
                st.markdown(f"**Expected Duration:** {plan['duration']}")
                st.markdown(f"**Isolation Guidelines:** {plan['isolation']}")
            
            if st.button("Start Tracking My Progress"):
                navigate_to("progress")
                st.experimental_rerun()
    
    with col2:
        st.markdown("### Quick Navigation")
        if st.button("🏠 Main Menu"):
            navigate_to("main")
        if st.button("📋 Treatment Plan"):
            navigate_to("treatment")
        if st.button("📊 Progress Tracking"):
            navigate_to("progress")
        if st.button("📚 Health Resources"):
            navigate_to("resources")
        
        st.markdown("### ℹ️ Health Tips")
        st.info("""
        - Wash hands frequently with soap and water
        - Practice social distancing
        - Wear masks in crowded places
        - Get vaccinated when available
        - Disinfect frequently touched surfaces
        """)
        
        st.markdown("### 🔔 Today's Reminders")
        st.markdown("""
        <div class="reminder-card">
            <b>Medication</b><br>
            Take prescribed medication after meals
        </div>
        <div class="reminder-card">
            <b>Hydration</b><br>
            Drink at least 8 glasses of water today
        </div>
        <div class="reminder-card">
            <b>Symptom Check</b><br>
            Record your symptoms and rating
        </div>
        """, unsafe_allow_html=True)

# Function to show treatment plan page
def show_treatment_plan():
    st.markdown("""
    <div class="logo-container">
        <div class="logo">📋</div>
        <h2 style="color: #0074D9;">Your Treatment Plan</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.treatment_plan:
        st.warning("Please complete the AI doctor consultation first to generate your treatment plan")
        if st.button("Go to Consultation"):
            navigate_to("consultation")
            st.experimental_rerun()
        return
    
    plan = st.session_state.treatment_plan
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Medication Schedule")
        med_data = []
        for i, med in enumerate(plan["medication"]):
            med_data.append({
                "Medication": med,
                "Dosage": "As prescribed" if i == 0 else "As needed",
                "Frequency": "Twice daily" if i == 0 else "When needed"
            })
        st.table(pd.DataFrame(med_data))
        
        st.markdown("### Diet Recommendations")
        st.info(plan["diet"])
        
        st.markdown("### Rest Guidelines")
        st.warning(plan["rest"])
    
    with col2:
        st.markdown("### Monitoring Instructions")
        st.info(plan["monitoring"])
        
        st.markdown("### Follow-up Plan")
        st.success(plan["follow_up"])
        
        st.markdown("### Expected Duration")
        st.info(plan["duration"])
        
        st.markdown("### Isolation Guidelines")
        st.warning(plan["isolation"])
    
    if st.button("Back to Consultation"):
        navigate_to("consultation")
        st.experimental_rerun()

# Function to show progress tracking page
def show_progress_tracking():
    st.markdown("""
    <div class="logo-container">
        <div class="logo">📊</div>
        <h2 style="color: #0074D9;">Your Progress Tracking</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.treatment_plan:
        st.warning("Please complete the AI doctor consultation first to track your progress")
        if st.button("Go to Consultation"):
            navigate_to("consultation")
            st.experimental_rerun()
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Daily Check-in")
        today = datetime.date.today()
        
        if today not in [entry['date'] for entry in st.session_state.progress_data.get('daily_rating', [])]:
            st.subheader("How are you feeling today?")
            rating = st.slider("Rate your symptoms (1-10)", 1, 10, 5, key="daily_rating")
            symptoms = st.multiselect("Current symptoms", 
                                     ["Fever", "Cough", "Headache", "Fatigue", "Body aches", "Shortness of breath", "Loss of taste/smell"])
            meds_taken = st.checkbox("I took my medication as prescribed")
            
            if st.button("Save Today's Progress", key="save_progress"):
                if 'daily_rating' not in st.session_state.progress_data:
                    st.session_state.progress_data['daily_rating'] = []
                
                st.session_state.progress_data['daily_rating'].append({
                    'date': today,
                    'rating': rating
                })
                
                st.session_state.progress_data['symptoms_track'].append({
                    'date': today,
                    'symptoms': symptoms
                })
                
                st.session_state.progress_data['medication_taken'].append({
                    'date': today,
                    'taken': meds_taken
                })
                
                st.success("Progress saved!")
                time.sleep(1)
                st.experimental_rerun()
        else:
            st.success("You've already completed today's check-in!")
        
        # Show progress history
        if st.session_state.progress_data.get('daily_rating'):
            st.markdown("### Your Progress History")
            progress_df = pd.DataFrame(st.session_state.progress_data['daily_rating'])
            st.line_chart(progress_df.set_index('date')['rating'])
    
    with col2:
        st.markdown("### Medication Adherence")
        if st.session_state.progress_data.get('medication_taken'):
            adherence = sum(1 for entry in st.session_state.progress_data['medication_taken'] if entry['taken'])
            total = len(st.session_state.progress_data['medication_taken'])
            st.markdown(f"**Adherence rate: {adherence}/{total} days ({adherence/total*100:.0f}%)**")
            
            adherence_data = [1 if entry['taken'] else 0 for entry in st.session_state.progress_data['medication_taken']]
            dates = [entry['date'] for entry in st.session_state.progress_data['medication_taken']]
            adherence_df = pd.DataFrame({'date': dates, 'adherence': adherence_data})
            st.bar_chart(adherence_df.set_index('date'))
        else:
            st.info("No medication data yet. Complete your daily check-in.")
        
        st.markdown("### Symptom History")
        if st.session_state.progress_data.get('symptoms_track'):
            symptom_history = []
            for entry in st.session_state.progress_data['symptoms_track']:
                for symptom in entry['symptoms']:
                    symptom_history.append({'date': entry['date'], 'symptom': symptom})
            
            if symptom_history:
                symptom_df = pd.DataFrame(symptom_history)
                symptom_pivot = pd.crosstab(symptom_df['date'], symptom_df['symptom'])
                st.bar_chart(symptom_pivot)
    
    if st.button("Back to Consultation"):
        navigate_to("consultation")
        st.experimental_rerun()

# Function to show health resources page
def show_health_resources():
    st.markdown("""
    <div class="logo-container">
        <div class="logo">📚</div>
        <h2 style="color: #0074D9;">Health Resources</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Informational Resources")
        with st.expander("Understanding Epidemic Diseases"):
            st.write("""
            Epidemic diseases spread rapidly through populations. Common examples include:
            - Influenza (Flu)
            - COVID-19
            - Dengue Fever
            - Monkeypox
            - Zika Virus
            
            Early detection and proper management are crucial for recovery.
            """)
        
        with st.expander("Prevention Guidelines"):
            st.write("""
            1. Practice good hand hygiene
            2. Maintain social distancing
            3. Wear masks in public spaces
            4. Get vaccinated when available
            5. Disinfect frequently touched surfaces
            6. Avoid touching your face
            7. Stay home when feeling unwell
            8. Practice respiratory etiquette
            9. Ensure proper ventilation indoors
            10. Follow local health authority guidelines
            """)
        
        with st.expander("When to Seek Medical Help"):
            st.write("""
            Seek immediate medical attention if you experience:
            - Difficulty breathing or shortness of breath
            - Persistent chest pain or pressure
            - New confusion or inability to wake/stay awake
            - Pale, gray, or blue-colored skin, lips, or nail beds
            - Severe persistent pain
            - High fever that doesn't respond to medication
            - Dehydration symptoms (dizziness, dry mouth, little urination)
            """)
    
    with col2:
        st.markdown("### Emergency Contacts")
        st.markdown("""
        <div class="card">
            <h4>Local Health Department</h4>
            <p>Phone: 1-800-HELP-NOW</p>
        </div>
        <div class="card">
            <h4>Emergency Services</h4>
            <p>Phone: 911 (or local emergency number)</p>
        </div>
        <div class="card">
            <h4>24/7 Nurse Line</h4>
            <p>Phone: 1-800-NURSE-4U</p>
        </div>
        <div class="card">
            <h4>Poison Control</h4>
            <p>Phone: 1-800-222-1222</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Mental Health Support")
        st.markdown("""
        <div class="card">
            <h4>Crisis Text Line</h4>
            <p>Text HOME to 741741</p>
        </div>
        <div class="card">
            <h4>National Suicide Prevention Lifeline</h4>
            <p>Phone: 1-800-273-8255</p>
        </div>
        <div class="card">
            <h4>Disaster Distress Helpline</h4>
            <p>Phone: 1
