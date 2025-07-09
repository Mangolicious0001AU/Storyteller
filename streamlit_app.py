import streamlit as st
import openai
import fitz  # PyMuPDF
import tempfile
import json
from fpdf import FPDF
import io
import re

st.set_page_config(page_title="Showrunner AI", page_icon="🎬")
st.title("🎬 Showrunner App")
st.write("Upload a script or voice file, analyze scenes, generate visuals, extract characters, and explore voiceovers.")

openai.api_key = st.secrets["OPENAI_API_KEY"]

uploaded_file = st.file_uploader("📄 Upload script (.txt, .pdf, or .mp3)", type=["txt", "pdf", "mp3"])
prompt = st.text_input("💡 Enter a creative prompt or instruction:")
input_text = ""

# Extract text or transcribe
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
            temp_audio_path = temp_audio.name
        with st.spinner("Transcribing audio..."):
            try:
                with open(temp_audio_path, "rb") as audio_file:
                    transcript = openai.Audio.transcribe("whisper-1", audio_file)
                    input_text = transcript["text"]
            except Exception as e:
                st.error(f"❌ Failed to transcribe audio: {e}")
    else:
        input_text = uploaded_file.read().decode("utf-8")

    st.text_area("📖 Uploaded or Transcribed Content", input_text, height=200)

# Storyboard Generator
output_text = st.session_state.get("storyboard_output", "")
reroll_requested = False

def generate_storyboard(prompt_input):
    scene_extract_prompt = f"""Break this script into 5 visual moments, each as a scene description suitable for storyboard art. 
Each should include:
- Scene title
- Short description of what's happening
- Visual elements, setting, and character action
- Camera angle or framing

Script:
{prompt_input}"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": scene_extract_prompt}],
            temperature=0.9,
            max_tokens=1200
        )
        return response["choices"][0]["message"]["content"]
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

# Downloads for storyboard
if output_text:
    st.download_button("⬇️ Download Scenes as TXT", output_text, file_name="storyboard_scenes.txt", mime="text/plain")

    scene_data = {"prompt": prompt, "content": output_text}
    st.download_button("⬇️ Download Scenes as JSON", json.dumps(scene_data, indent=2), file_name="storyboard_scenes.json", mime="application/json")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Prompt:\n{prompt}\n\nGenerated Scenes:\n\n{output_text}")
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    st.download_button("⬇️ Download Scenes as PDF", data=pdf_output, file_name="storyboard_scenes.pdf", mime="application/pdf")

# TTS Voiceover
if output_text:
    st.markdown("---")
    st.subheader("🔊 AI Voiceover")
    selected_voice = st.selectbox("🎙 Choose a voice", options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"], index=0)
    if st.button("🎤 Generate Voiceover (.mp3)"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
                response = openai.audio.speech.create(model="tts-1", voice=selected_voice, input=output_text)
                response.stream_to_file(audio_file.name)
                st.audio(audio_file.name, format="audio/mp3")
                with open(audio_file.name, "rb") as f:
                    st.download_button("⬇️ Download Voiceover", f, file_name="voiceover.mp3")
        except Exception as e:
            st.error(f"Failed to generate voiceover: {e}")

# Character Extraction
if input_text:
    st.markdown("---")
    st.subheader("🧍 Character Detection")

    # Regex-based simple extractor
    pattern = re.findall(r"^\s*([A-Z][A-Z0-9\s\-]+):", input_text, re.MULTILINE)
    cleaned = sorted(set([name.strip().replace("  ", " ") for name in pattern if len(name.strip()) <= 30]))

    if cleaned:
        st.write(f"🎭 **Detected {len(cleaned)} character(s):**")
        st.code("\n".join(cleaned), language="text")

        # Prepare character role classification (basic)
        speakers = set(cleaned)
        mentions = set()
        for name in speakers:
            if name not in input_text:
                mentions.add(name)

        # Save character list
        char_block = "\n".join(cleaned)
        st.download_button("⬇️ Download Characters as TXT", char_block, file_name="character_list.txt", mime="text/plain")

        st.download_button(
            "⬇️ Download Characters as JSON",
            json.dumps({"characters": cleaned}, indent=2),
            file_name="character_list.json",
            mime="application/json"
        )

        # PDF version
        char_pdf = FPDF()
        char_pdf.add_page()
        char_pdf.set_font("Arial", size=12)
        char_pdf.multi_cell(0, 10, "Detected Characters:\n\n" + "\n".join(cleaned))
        char_pdf_io = io.BytesIO()
        char_pdf.output(char_pdf_io)
        char_pdf_io.seek(0)
        st.download_button("⬇️ Download Characters as PDF", data=char_pdf_io, file_name="character_list.pdf", mime="application/pdf")

elif prompt and not input_text:
    st.warning("⚠️ Please upload a file before generating.")

# Force redeploy: minor update