
import streamlit as st
import openai
import fitz  # PyMuPDF
import tempfile

st.set_page_config(page_title="Showrunner AI", page_icon="🎬")

st.title("🎬 Showrunner App")
st.write("Upload a script or voice file, analyze scenes, generate visuals, and explore styles.")

# Load OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

uploaded_file = st.file_uploader("📄 Upload script (.txt, .pdf, or .mp3)", type=["txt", "pdf", "mp3"])
prompt = st.text_input("💡 Enter a creative prompt or instruction:")
input_text = ""

# Extract text or transcribe audio
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        try:
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                input_text = "\n".join(page.get_text() for page in doc)
        except Exception as e:
            st.error(f"❌ Failed to read PDF: {e}")
            input_text = ""
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
                input_text = ""
    else:
        input_text = uploaded_file.read().decode("utf-8")

    st.text_area("📖 Uploaded or Transcribed Content", input_text, height=200)

# Visual Storyboard Generator
if st.button("🖼️ Generate Visual Storyboard") and input_text:
    with st.spinner("Extracting storyboard-worthy scenes..."):
        try:
            scene_extract_prompt = f"""Break this script into 5 visual moments, each as a scene description suitable for storyboard art. 
Each should include:
- Scene title
- Short description of what's happening
- Visual elements, setting, and character action
- Camera angle or framing

Script:
{input_text}"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": scene_extract_prompt}],
                temperature=0.7,
                max_tokens=1200
            )
            scenes = response["choices"][0]["message"]["content"]
            st.markdown("## 🖼️ Storyboard Scenes")
            st.text(scenes)

        except Exception as e:
            st.error(f"Storyboard generation failed: {e}")

elif prompt and not input_text:
    st.warning("⚠️ Please upload a file before generating.")

# Force redeploy: minor update