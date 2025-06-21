import streamlit as st
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader
from io import StringIO
import re
from dotenv import load_dotenv
import streamlit_authenticator as stauth

# App config
st.set_page_config(
    page_title="SG Career Atlas",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication
names = ["Individual User", "Career Coach", "HR Manager"]
usernames = ["individual", "coach", "manager"]
passwords = ["pass123", "pass456", "pass789"]
hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    names,
    usernames,
    hashed_passwords,
    "career_atlas",
    "abcdef",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login", "main")

if not authentication_status:
    st.stop()

# Session state
if 'persona' not in st.session_state:
    st.session_state.persona = username
if 'riasec_data' not in st.session_state:
    st.session_state.riasec_data = {}
if 'skills_data' not in st.session_state:
    st.session_state.skills_data = []

# Header with persona badge
st.title("SG Career Atlas")
col1, col2 = st.columns([4,1])
with col1:
    st.subheader("Your AI-powered Career Guide")
with col2:
    st.info(f"Persona: {name}")

# RIASEC Assessment
if not st.session_state.riasec_data:
    st.header("RIASEC Assessment")
    with st.form("riasec_form"):
        st.write("Rate each statement (1-5):")
        riasec_categories = {
            'Realistic': ["Working with hands/tools", "Building/repairing things"],
            'Investigative': ["Researching topics", "Solving complex problems"],
            'Artistic': ["Creating new ideas", "Expressing yourself creatively"],
            'Social': ["Helping others", "Teaching/training people"],
            'Enterprising': ["Leading others", "Selling ideas/products"],
            'Conventional': ["Organizing data", "Following clear procedures"]
        }
        
        responses = {}
        for category, questions in riasec_categories.items():
            st.subheader(category)
            for q in questions:
                responses[f"{category}_{q}"] = st.slider(q, 1, 5, 3)
        
        if st.form_submit_button("Submit Assessment"):
            st.session_state.riasec_data = responses
            st.rerun()
else:
    # Results Visualization
    st.header("Your Assessment Results")
    
    # Calculate category averages
    category_scores = {}
    for category in riasec_categories.keys():
        cat_responses = [v for k,v in st.session_state.riasec_data.items() if k.startswith(category)]
        category_scores[category] = sum(cat_responses)/len(cat_responses)
    
    # Radar chart
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})
    categories = list(category_scores.keys())
    values = list(category_scores.values())
    values += values[:1]  # Close the radar chart
    
    angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
    angles += angles[:1]
    
    ax.plot(angles, values, linewidth=1, linestyle='solid')
    ax.fill(angles, values, 'b', alpha=0.1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title("RIASEC Profile", size=20)
    
    st.pyplot(fig)
    
    # Recommendations
    st.header("Personalized Recommendations")
    
    top_category = max(category_scores, key=category_scores.get)
    st.subheader(f"Your Top Area: {top_category}")
    
    recommendations = {
        'Realistic': "Consider hands-on roles like engineering technicians or skilled trades",
        'Investigative': "Explore research-based careers in science or data analysis",
        'Artistic': "Creative fields like design or content creation may suit you",
        'Social': "Look into helping professions like teaching or counseling",
        'Enterprising': "Leadership roles in business or sales could be a good fit",
        'Conventional': "Structured environments like accounting or administration may appeal"
    }
    
    st.write(recommendations[top_category])
    
    if st.button("Retake Assessment"):
        st.session_state.riasec_data = {}
        st.rerun()

# File Uploader (only for certain personas)
if st.session_state.persona in ["coach", "manager"]:
    st.header("Upload Career Data")
    uploaded_files = st.file_uploader(
        "Upload CSV/TXT/PDF files with job skills data",
        type=['csv', 'txt', 'pdf'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for file in uploaded_files:
            processed = process_file(file)
            st.session_state.skills_data.append(processed)
        st.success(f"Processed {len(uploaded_files)} files")

# Logout
authenticator.logout("Logout", "sidebar")
