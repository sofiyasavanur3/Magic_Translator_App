import streamlit as st
import openai
from gtts import gTTS
import PyPDF2
import io
import docx

# Set up the page
st.set_page_config(
    page_title="Magic Translator",
    page_icon="🌍",
    layout="wide"
)

# Set OpenAI API key
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except Exception as e:
    st.error("⚠️ OpenAI API key not found! Please add it to .streamlit/secrets.toml")
    st.error(f"Error: {str(e)}")
    st.stop()

# Title
st.title("🌍 Magic Translator & Text-to-Speech")
st.write("Translate text into different languages and hear it spoken!")

# Sidebar for instructions
with st.sidebar:
    st.header("📖 How to Use")
    st.write("1. Type or upload text (TXT, PDF, DOCX)")
    st.write("2. Select target language")
    st.write("3. Click 'Translate & Speak'")
    st.write("4. Listen to the audio")
    st.write("5. Download the audio file!")
    
    st.divider()
    st.header("ℹ️ About")
    st.write("This app uses:")
    st.write("• OpenAI GPT-3.5 for translation")
    st.write("• Google Text-to-Speech for audio")
    st.write("• Streamlit for the interface")

# Language mapping
languages = {
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Japanese": "ja",
    "Chinese (Simplified)": "zh-cn",
    "Arabic": "ar",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Korean": "ko"
}

# Function to extract text from PDF
def extract_pdf_text(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

# Function to extract text from DOCX
def extract_docx_text(docx_file):
    try:
        doc = docx.Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading DOCX: {str(e)}")
        return None

# Function to translate text
def translate_text(text, target_language):
    try:
        with st.spinner("🔄 Translating..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional translator. Translate the given text accurately to the target language. Only provide the translation, no explanations."},
                    {"role": "user", "content": f"Translate this text to {target_language}:\n\n{text}"}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None

# Function to create speech
def text_to_speech(text, lang_code):
    try:
        with st.spinner("🎤 Creating audio..."):
            tts = gTTS(text=text, lang=lang_code, slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer
    except Exception as e:
        st.error(f"Text-to-speech error: {str(e)}")
        return None

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Input Text")
    
    # Tab for text input or file upload
    tab1, tab2 = st.tabs(["✍️ Type Text", "📄 Upload File"])
    
    with tab1:
        user_input = st.text_area(
            "Type your text here:",
            height=250,
            placeholder="Enter the text you want to translate..."
        )
    
    with tab2:
        uploaded_file = st.file_uploader(
            "Upload a file (TXT, PDF, DOCX)",
            type=['txt', 'pdf', 'docx']
        )
        
        if uploaded_file:
            file_type = uploaded_file.type
            
            if file_type == "text/plain":
                user_input = uploaded_file.read().decode("utf-8")
                st.success("✅ Text file loaded!")
                
            elif file_type == "application/pdf":
                user_input = extract_pdf_text(uploaded_file)
                if user_input:
                    st.success("✅ PDF file loaded!")
                    
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                user_input = extract_docx_text(uploaded_file)
                if user_input:
                    st.success("✅ Word document loaded!")
            
            if user_input:
                with st.expander("👀 Preview extracted text"):
                    st.write(user_input[:500] + ("..." if len(user_input) > 500 else ""))

with col2:
    st.header("⚙️ Settings")
    selected_language = st.selectbox(
        "Choose target language:",
        list(languages.keys()),
        index=0
    )
    
    lang_code = languages[selected_language]
    
    st.info(f"🎯 Translating to: **{selected_language}**")
    
    # Character count
    if 'user_input' in locals() and user_input:
        char_count = len(user_input)
        st.metric("Character Count", char_count)
        
        if char_count > 5000:
            st.warning("⚠️ Text is quite long. Translation may take a moment.")

# Translate button
st.divider()

if st.button("🚀 Translate & Speak", type="primary", use_container_width=True):
    if 'user_input' not in locals() or not user_input:
        st.error("⚠️ Please enter some text or upload a file first!")
    else:
        # Translate
        translated_text = translate_text(user_input, selected_language)
        
        if translated_text:
            # Display results
            st.success("✅ Translation complete!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📄 Original Text")
                st.text_area("", user_input, height=200, key="original", disabled=True)
            
            with col2:
                st.subheader(f"🌍 Translated Text ({selected_language})")
                st.text_area("", translated_text, height=200, key="translated", disabled=True)
            
            # Create audio
            audio_data = text_to_speech(translated_text, lang_code)
            
            if audio_data:
                st.divider()
                st.subheader("🔊 Listen to Translation")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.audio(audio_data, format="audio/mp3")
                
                with col2:
                    st.download_button(
                        label="⬇️ Download Audio",
                        data=audio_data,
                        file_name=f"translation_{selected_language.lower()}.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
                
                st.success("🎉 All done! You can now listen or download the audio.")

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Made with ❤️ using Streamlit | Powered by OpenAI & Google TTS</p>
    </div>
    """,
    unsafe_allow_html=True
)