import streamlit as st
import pandas as pd
import datetime
import time
import random
import pyttsx3
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="EpidemicCare AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the questions flow
questions = [
    "What is your name?",
    "How old are you?",
    "Do you have any pre-existing medical conditions?",
    "Have you had a fever in the last 48 hours?",
    "Are you experiencing any cough or difficulty breathing?",
    "Do you have any body aches or joint pain?",
    "Have you noticed any loss of taste or smell?",
    "Are you experiencing fatigue or unusual tiredness?",
    "Any other symptoms you'd like to mention?"
]

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

# ================== AI Doctor Responses ==================
def get_ai_response(step, user_input=None):
    responses = {
        0: "Hello! I'm Dr. AI, your medical assistant. What's your name?",
        1: f"Nice to meet you, {user_input}! How old are you?",
        2: "Do you have any pre-existing medical conditions?",
        3: "Have you had a fever in the last 48 hours?",
        4: "Are you experiencing any cough or difficulty breathing?",
        5: "Do you have any body aches or joint pain?",
        6: "Have you noticed any loss of taste or smell?",
        7: "Are you experiencing fatigue or unusual tiredness?",
        8: "Any other symptoms you'd like to mention?",
        9: "Thank you. I'm now analyzing your symptoms...",
        10: "Based on your symptoms, I'm developing a personalized treatment plan for you.",
        11: "I've prepared a comprehensive treatment plan. Let me walk you through it."
    }
    return responses.get(step, "Please tell me more about your health.")

# ================== Voice (TTS) ==================
def speak_text(text):
    """Convert text to speech and return audio file path"""
    engine = pyttsx3.init()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        engine.save_to_file(text, tmp.name)
        engine.runAndWait()
        return tmp.name

# ================== Chat UI ==================
def display_chat():
    for sender, message in st.session_state.chat_history:
        if sender == "doctor":
            st.markdown(f"💙 **Dr. AI:** {message}")
        else:
            st.markdown(f"🧑 **You:** {message}")

# ================== Doctor Consultation ==================
def show_ai_doctor():
    st.title("🩺 EpidemicCare AI Doctor")

    display_chat()

    if st.session_state.current_step < len(questions):
        current_question = get_ai_response(st.session_state.current_step, st.session_state.symptoms.get('name'))

        # Add to history if not already added
        if not st.session_state.chat_history or st.session_state.chat_history[-1][1] != current_question:
            st.session_state.chat_history.append(("doctor", current_question))

            # Generate and play voice
            audio_file = speak_text(current_question)
            st.audio(audio_file, format="audio/mp3")

        # Handle different steps
        if st.session_state.current_step == 0:
            name = st.text_input("Your name", key="input_name")
            if st.button("Submit Name"):
                st.session_state.symptoms['name'] = name
                st.session_state.chat_history.append(("user", name))
                st.session_state.current_step += 1
                st.experimental_rerun()

        elif st.session_state.current_step == 1:
            age = st.number_input("Your age", min_value=0, max_value=120, key="input_age")
            if st.button("Submit Age"):
                st.session_state.symptoms['age'] = age
                st.session_state.chat_history.append(("user", str(age)))
                st.session_state.current_step += 1
                st.experimental_rerun()

        elif st.session_state.current_step == 2:
            conditions = st.text_input("Any pre-existing conditions?", key="input_cond")
            if st.button("Submit Conditions"):
                st.session_state.symptoms['conditions'] = conditions
                st.session_state.chat_history.append(("user", conditions if conditions else "None"))
                st.session_state.current_step += 1
                st.experimental_rerun()
        else:
            options = ["Yes", "No", "Not sure"]
            response = st.radio("Choose:", options, key=f"input_{st.session_state.current_step}")
            if st.button("Submit Answer", key=f"btn_{st.session_state.current_step}"):
                st.session_state.symptoms[f'symptom_{st.session_state.current_step}'] = response
                st.session_state.chat_history.append(("user", response))
                st.session_state.current_step += 1
                st.experimental_rerun()
    else:
        st.success("✅ Consultation finished! AI Doctor will now analyze your symptoms.")
        st.write("👉 You can now extend logic here to generate diagnosis, risk assessment, and treatment plan.")

# ================== Main Page ==================
def show_welcome():
    st.title("🩺 EpidemicCare AI")
    st.write("Your AI-powered epidemic disease assistant.")
    if st.button("Start Consultation"):
        st.session_state.page = "consultation"
        st.experimental_rerun()

# ================== Router ==================
if st.session_state.page == "welcome":
    show_welcome()
elif st.session_state.page == "consultation":
    show_ai_doctor()
