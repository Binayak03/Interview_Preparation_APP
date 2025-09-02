import streamlit as st
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY not found. Please set it in .env or environment variables.")
    st.stop()

# Set up the AI client
client = Groq(api_key=api_key)

# App title
st.title("AI-Powered Interview App")

# Let user upload a resume PDF
uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")

if uploaded_file is not None:
    # Parse the resume
    with pdfplumber.open(uploaded_file) as pdf:
        resume_text = ""
        for page in pdf.pages:
            resume_text += page.extract_text() or ""

    st.success("Resume uploaded and parsed!")

    # Step 1: Analyze resume
    analysis_prompt = f"Extract key experience, skills, and projects from this resume text. Be concise: {resume_text}"
    analysis_response = client.chat.completions.create(
        messages=[{"role": "user", "content": analysis_prompt}],
        model="llama-3.1-8b-instant"
    )
    resume_analysis = analysis_response.choices[0].message.content
    st.write("**Resume Analysis:**")
    st.write(resume_analysis)

    # Step 2: Generate questions for each category
    question_categories = {
        "General Questions": {
            "count": 5,
            "prompt": f"Based on this resume analysis, generate exactly 5 relevant interview questions for a software engineer role focusing on AI and health tech: {resume_analysis}. Format each question as 'Q#: <question text>' with no additional explanations or headers."
        },
        "Critical Thinking Questions": {
            "count": 5,
            "prompt": f"Based on this resume analysis, generate exactly 5 critical thinking interview questions for a software engineer role focusing on AI and health tech. Questions should test problem-solving, decision-making, or handling trade-offs: {resume_analysis}. Format each question as 'Q#: <question text>' with no additional explanations or headers."
        },
        "Computer Science Questions": {
            "count": 5,
            "prompt": f"Based on this resume analysis, generate exactly 5 computer science interview questions (basic to advanced) for a software engineer role focusing on AI and health tech. Cover topics like OOP, databases, or system design: {resume_analysis}. Format each question as 'Q#: <question text>' with no additional explanations or headers."
        },
        "DSA Question": {
            "count": 1,
            "prompt": f"Based on this resume analysis, generate exactly 1 data structures and algorithms interview question for a software engineer role focusing on AI and health tech. Focus on a practical problem (e.g., trees, sorting): {resume_analysis}. Format as 'Q#: <question text>' with no additional explanations or headers."
        },
        "AI Questions": {
            "count": 4,
            "prompt": f"Based on this resume analysis, generate exactly 4 AI interview questions (basic to advanced) for a software engineer role focusing on AI and health tech. Cover topics like machine learning basics, model optimization, or deployment: {resume_analysis}. Format each question as 'Q#: <question text>' with no additional explanations or headers."
        }
    }

    # Initialize scores
    if "scores" not in st.session_state:
        st.session_state.scores = []
    if "all_questions" not in st.session_state:
        st.session_state.all_questions = []

    # Generate and display questions for each category
    question_index = 1  # Unified question numbering across categories
    for category, config in question_categories.items():
        st.subheader(category)
        # Generate questions
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": config["prompt"]}],
            model="llama-3.1-8b-instant"
        )
        response_text = response.choices[0].message.content
        questions = re.findall(r'Q\d+:\s*(.*?)(?=\nQ\d+:|\n*$)', response_text, re.DOTALL)
        questions = [q.strip() for q in questions if q.strip()][:config["count"]]

        if len(questions) < config["count"]:
            st.error(f"Failed to generate {config['count']} questions for {category}. Got {len(questions)} questions.")
            st.write("Raw API response:", response_text)
            st.stop()

        # Store questions in session state
        st.session_state.all_questions.extend(questions)

        # Display and collect answers
        for i, question in enumerate(questions):
            st.write(f"**Question {question_index}:** {question}")
            answer = st.text_input(f"Your answer to question {question_index}:", key=f"answer_{question_index}")
            if answer:
                # Analyze the answer
                analyze_prompt = (
                    f"Question: {question}\nAnswer: {answer}\n"
                    f"Analyze how well this answers the question for a software engineer role in AI and health tech. "
                    f"Provide a score from 1-10 (10 is excellent) and a brief reason. "
                    f"Format the response as: 'Score: X\nReason: <reason>'"
                )
                analyze_response = client.chat.completions.create(
                    messages=[{"role": "user", "content": analyze_prompt}],
                    model="llama-3.1-8b-instant"
                )
                analysis = analyze_response.choices[0].message.content
                st.write(f"**Analysis:** {analysis}")

                # Extract score
                try:
                    score = int(analysis.split("Score:")[1].strip().split("\n")[0])
                    st.session_state.scores.append(score)
                except:
                    st.error("Couldn't parse score. Try again.")
            question_index += 1

    # Step 3: Final decision
    if len(st.session_state.scores) == len(st.session_state.all_questions):
        avg_score = sum(st.session_state.scores) / len(st.session_state.scores)
        st.write(f"**Average Score:** {avg_score:.2f}/10")
        if avg_score >= 7:
            st.success("Congratulations! You are selected for the software engineer role in AI and health tech.")
        else:
            st.warning("Sorry, you are not selected. Keep practicing!")