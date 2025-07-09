
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
output_text = st.session_state.get("storyboard_output", "")
reroll_requested = False

def generate_storyboard(prompt_input):
    try:
        scene_extract_prompt = f"""Break this script into 5 visual moments, each as a scene description suitable for storyboard art. 
Each should include:
- Scene title
- Short description of what's happening
- Visual elements, setting, and character action
- Camera angle or framing

Script:
{prompt_input}"""

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
    reroll_requested = True
    with st.spinner("Generating alternate storyboard..."):
        output_text = generate_storyboard(input_text)
        st.session_state["storyboard_output"] = output_text

if output_text:
    st.markdown("## 🖼️ Storyboard Scenes")
    st.text(output_text)

# TTS Voiceover from Generated Scenes
if output_text:
    st.markdown("---")
    st.subheader("🔊 AI Voiceover")

    selected_voice = st.selectbox("🎙 Choose a voice", options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"], index=0)

    if st.button("🎤 Generate Voiceover (.mp3)"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
                response = openai.audio.speech.create(
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

elif prompt and not input_text:
    st.warning("⚠️ Please upload a file before generating.")

# Force redeploy: minor update