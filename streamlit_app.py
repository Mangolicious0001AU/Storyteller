
import streamlit as st
import tempfile
import fitz  # PyMuPDF
from openai import OpenAI
from fpdf import FPDF
import json
import io
import os

# Setup
st.set_page_config(page_title="Showrunner AI", page_icon="🎬")
st.title("🎬 Showrunner App")
st.write("Upload a script or voice file, analyze scenes, generate visuals, and explore styles.")

# Load API Key and Client
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Upload
uploaded_file = st.file_uploader("📄 Upload script (.txt, .pdf, or .mp3)", type=["txt", "pdf", "mp3"])
prompt = st.text_input("💡 Enter a creative prompt or instruction:")
input_text = ""

# Extract / Transcribe
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        try:
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                input_text = "\n".join(page.get_text() for page in doc)
        except Exception as e:
            st.error(f"❌ Failed to read PDF: {e}")
    elif uploaded_file.type == "audio/mpeg":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(uploaded_file.read())
            temp_path = temp_audio.name

        with st.spinner("Transcribing audio..."):
            try:
                with open(temp_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                    input_text = transcript.text
            except Exception as e:
                st.error(f"❌ Failed to transcribe audio: {e}")
    else:
        input_text = uploaded_file.read().decode("utf-8")

    st.text_area("📖 Uploaded or Transcribed Content", input_text, height=200)

# Visual Storyboard Generator
output_text = st.session_state.get("storyboard_output", "")
reroll_requested = False

def generate_storyboard(prompt_input):
    try:
        full_prompt = f"""Break this script into 5 visual moments, each as a scene description suitable for storyboard art.
Each should include:
- Scene title
- Short description
- Visual elements, setting, and character action
- Camera angle or framing

Script:
{prompt_input}"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.9,
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Storyboard generation failed: {e}")
        return ""

if st.button("🖼️ Generate Visual Storyboard") and input_text:
    with st.spinner("Extracting storyboard-worthy scenes..."):
        output_text = generate_storyboard(input_text)
        st.session_state["storyboard_output"] = output_text

if st.button("🔁 Reroll Alternate Take") and input_text:
    with st.spinner("Generating alternate storyboard..."):
        output_text = generate_storyboard(input_text)
        st.session_state["storyboard_output"] = output_text

if output_text:
    # Downloads
    st.download_button("⬇️ Download Scenes as TXT", output_text, file_name="storyboard_scenes.txt", mime="text/plain")

    scene_data = {"prompt": prompt, "content": output_text}
    st.download_button("⬇️ Download Scenes as JSON", json.dumps(scene_data, indent=2), file_name="storyboard_scenes.json", mime="application/json")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Prompt:\n{prompt}\n\nGenerated Scenes:\n\n{output_text}")
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    st.download_button("⬇️ Download Scenes as PDF", data=pdf_buffer, file_name="storyboard_scenes.pdf", mime="application/pdf")

# TTS Voiceover
if output_text:
    st.markdown("---")
    st.subheader("🔊 AI Voiceover")
    selected_voice = st.selectbox("🎙 Choose a voice", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    if st.button("🎤 Generate Voiceover (.mp3)"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=selected_voice,
                    input=output_text
                )
                response.stream_to_file(audio_file.name)
                st.audio(audio_file.name, format="audio/mp3")
                with open(audio_file.name, "rb") as f:
                    st.download_button("⬇️ Download Voiceover", f, file_name="voiceover.mp3")
        except Exception as e:
            st.error(f"Failed to generate voiceover: {e}")

# Character Detection
if input_text:
    with st.expander("🧍 Character List (Auto-Detected)"):
        try:
            char_prompt = f"""From the script below, extract a list of characters.
- Separate into: Speaking Roles and Background Mentions
- Format names in ALL CAPS
- Remove duplicates and sort alphabetically

Script:
{input_text}"""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": char_prompt}],
                temperature=0.3,
                max_tokens=700
            )

            character_list = response.choices[0].message.content.strip()
            st.text_area("🎭 Detected Characters", character_list, height=200)

            # Export
            st.download_button("⬇️ Download as TXT", character_list, file_name="characters.txt", mime="text/plain")
            st.download_button("⬇️ Download as JSON", json.dumps({"characters": character_list}, indent=2), file_name="characters.json", mime="application/json")

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, f"Detected Characters:\n\n{character_list}")
            pdf_io = io.BytesIO()
            pdf.output(pdf_io)
            pdf_io.seek(0)
            st.download_button("⬇️ Download as PDF", data=pdf_io, file_name="characters.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"❌ Failed to extract characters: {e}")

elif prompt and not input_text:
    st.warning("⚠️ Please upload a file before generating.")

# Force redeploy: minor update