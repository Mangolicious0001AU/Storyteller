
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

# Read uploaded file
if uploaded_file is not None:
    input_text = uploaded_file.read().decode("utf-8")
    st.text_area("📖 Uploaded File Content", input_text, height=200)

# Trigger generation
if prompt and input_text:
    if st.button("⚡ Generate Draft"):
        with st.spinner("Calling the AI Showrunner..."):
            try:
                # Call OpenAI API
                full_prompt = f"{prompt}

---

{input_text}"
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                output_text = response["choices"][0]["message"]["content"]
                st.success("✅ Draft generated successfully!")
                st.text_area("📝 AI-Generated Script", output_text, height=300)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
elif prompt and not input_text:
    st.warning("⚠️ Please upload a file before generating.")
