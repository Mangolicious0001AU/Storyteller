
import streamlit as st
import openai

st.set_page_config(page_title="Showrunner AI", page_icon="🎬")

st.title("🎬 Showrunner App")
st.write("Upload a script or idea, enter a prompt, and generate creative outputs.")

# Load OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# UI elements
uploaded_file = st.file_uploader("📄 Upload a script or idea (.txt)", type=["txt"])
prompt = st.text_input("💡 Enter a prompt or instruction:")

input_text = ""
output_text = st.session_state.get("output_text", "")

# Read uploaded file
if uploaded_file is not None:
    input_text = uploaded_file.read().decode("utf-8")
    st.text_area("📖 Uploaded File Content", input_text, height=200)

# Function to call OpenAI
def generate_output():
    full_prompt = f"""{prompt}

---

{input_text}"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response["choices"][0]["message"]["content"]

# Buttons to generate and reroll
if prompt and input_text:
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⚡ Generate Draft"):
            with st.spinner("Calling the AI Showrunner..."):
                output_text = generate_output()
                st.session_state["output_text"] = output_text
                st.success("✅ Draft generated successfully!")

    with col2:
        if st.button("🔁 Reroll"):
            with st.spinner("Getting a fresh take..."):
                output_text = generate_output()
                st.session_state["output_text"] = output_text
                st.success("🔄 Reroll complete!")

    if output_text:
        st.markdown("### 📝 AI-Generated Script", unsafe_allow_html=True)
        st.markdown(output_text)
        st.download_button("💾 Download Script", output_text, file_name="script.txt")
elif prompt and not input_text:
    st.warning("⚠️ Please upload a file before generating.")

# Force redeploy: minor update