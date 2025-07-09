# Character Detection and Export
if input_text:
    with st.expander("🧍 Character List (Auto-Detected)"):
        try:
            character_prompt = f"""From the script below, extract a list of characters.
- Separate into two lists: Speaking Roles and Background Mentions
- Format names in ALL CAPS
- Remove duplicates, sort alphabetically

Script:
{input_text}
"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": character_prompt}],
                temperature=0.3,
                max_tokens=700
            )

            character_list = response["choices"][0]["message"]["content"]
            st.text_area("🎭 Detected Characters", character_list, height=200)

            # Export Options
            st.download_button(
                "⬇️ Download as TXT",
                character_list,
                file_name="characters.txt",
                mime="text/plain"
            )

            import json
            char_json = {"characters": character_list}
            st.download_button(
                "⬇️ Download as JSON",
                json.dumps(char_json, indent=2),
                file_name="characters.json",
                mime="application/json"
            )

            from fpdf import FPDF
            import io

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, f"Detected Characters:\n\n{character_list}")
            char_pdf = io.BytesIO()
            pdf.output(char_pdf)
            char_pdf.seek(0)
            st.download_button(
                "⬇️ Download as PDF",
                data=char_pdf,
                file_name="characters.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Failed to extract characters: {e}")

# Force redeploy: minor update