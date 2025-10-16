import streamlit as st
import assemblyai as aai
import os
import tempfile
import re
from urllib.parse import urlparse, parse_qs
import requests
from pytube import YouTube

# Configure AssemblyAI API key
aai.settings.api_key = st.session_state.get("ASSEMBLYAI_API_KEY", None)

def is_youtube_url(url):
    """Check if the given string is a YouTube URL"""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return re.match(youtube_regex, url) is not None

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be',):
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query)['v'][0]
        if parsed.path.startswith(('/embed/', '/v/')):
            return parsed.path.split('/')[2]
    return None

def transcribe_audio(audio_file_path):
    """Transcribe audio/video file using AssemblyAI API"""
    try:
        config = aai.TranscriptionConfig(speaker_labels=True)
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_file_path)
        
        if transcript.status == aai.TranscriptStatus.error:
            st.error(f"Transcription failed: {transcript.error}")
            return None
        else:
            return transcript.text
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return None

def transcribe_youtube(youtube_url):
    """Transcribe YouTube video using AssemblyAI API"""
    try:
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            audio_stream.stream_to_buffer(tmp_file)
            tmp_file.seek(0)
            return transcribe_audio(tmp_file.name)

    except Exception as e:
        st.error(f"YouTube transcription error: {str(e)}")
        return None

def summarize_text(text):
    """Summarize text using extractive summarization"""
    try:
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) > 4:
            # Take first, middle, and last sentences for better summary
            summary_sentences = [
                sentences[0],
                sentences[len(sentences)//3],
                sentences[len(sentences)//2],
                sentences[-2] if len(sentences) > 2 else sentences[-1]
            ]
            summary = '. '.join(summary_sentences) + '.'
        elif len(sentences) > 1:
            summary = '. '.join(sentences[:2]) + '.'
        else:
            summary = text
        return summary
    except Exception as e:
        st.error(f"Summarization error: {str(e)}")
        return text

import openai

def translate_to_kanglish_with_llm(english_text):
    """Translate English text to Kanglish using a Large Language Model."""
    openrouter_api_key = st.session_state.get("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        st.error("OpenRouter API key not found. Please set it in the Settings page.")
        return "Translation failed: API key is missing."

    try:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )

        prompt = f"""
        Translate the following English text into Kanglish. Kanglish is a mix of Kannada and English, where Kannada words are written in the English alphabet (transliterated). The goal is to make the text sound natural for a person from Karnataka, India, who speaks both languages.

        Guidelines:
        1.  Keep the sentence structure mostly English.
        2.  Translate key nouns, verbs, and adjectives into Kannada, but keep conjunctions, prepositions, and technical terms in English.
        3.  The final output must be easy to read and sound like a casual conversation.
        4.  Do not provide any explanation, just the translated text.

        English Text:
        "{english_text}"

        Kanglish Translation:
        """

        response = client.chat.completions.create(
            model="deepseek/deepseek-coder",
            messages=[
                {"role": "system", "content": "You are an expert translator specializing in creating natural-sounding Kanglish."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"LLM Translation error: {str(e)}")
        return "Translation failed due to an API error."

def main():
    st.set_page_config(
        page_title="Kannada Audio Bridge",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for professional appearance
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 600;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-bottom: 1rem;
        font-weight: 500;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.5rem;
    }
    .success-box {
        background-color: #f0f9ff;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #2e86ab;
        margin: 15px 0;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #6c757d;
        margin: 15px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
        margin: 10px 0;
    }
    .input-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border: 2px dashed #dee2e6;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Application Header
    st.markdown('<h1 class="main-header">Kannada Audio Bridge</h1>', unsafe_allow_html=True)
    st.markdown("### Convert English content to summarized Kanglish output")
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        
        app_mode = st.radio(
            "Select Function:",
            ["Home", "Input Content", "Processing Results", "Settings"]
        )
        
        st.markdown("---")
        st.markdown("### Application Information")
        st.info(
            "Supports MP4, MP3 files, YouTube URLs, and plain text input. "
            "Converts English content to accessible Kanglish summaries."
        )
        
        # API Status
        if aai.settings.api_key and aai.settings.api_key != "YOUR_ASSEMBLYAI_API_KEY_HERE":
            st.success("AssemblyAI API: Configured")
        else:
            st.error("AssemblyAI API: Not Configured")
            st.markdown("""
            To use audio features:
            1. Get an API key from [AssemblyAI](https://www.assemblyai.com/)
            2. Set it in the Settings page
            """)

    # Main content based on navigation
    if app_mode == "Home":
        show_home_page()
    elif app_mode == "Input Content":
        show_input_page()
    elif app_mode == "Processing Results":
        show_processing_page()
    elif app_mode == "Settings":
        show_settings_page()

def show_home_page():
    """Display the home page with application overview"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### Overview")
        st.write(
            "This application converts English audio and text content into "
            "accessible Kannada-English (Kanglish) summaries. Support for multiple "
            "input formats makes it easy to process various types of content."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### Supported Input Formats")
        
        formats = [
            {"title": "Audio Files", "desc": "MP3, WAV, M4A, OGG formats"},
            {"title": "Video Files", "desc": "MP4 files with audio content"},
            {"title": "YouTube URLs", "desc": "Direct links to YouTube videos"},
            {"title": "Plain Text", "desc": "Copy-paste English text directly"}
        ]
        
        for format_info in formats:
            with st.container():
                st.markdown(f'<div class="info-box">', unsafe_allow_html=True)
                st.markdown(f"**{format_info['title']}**")
                st.write(format_info['desc'])
                st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Processing Pipeline")
        
        steps = [
            "Input: Upload file, paste URL, or enter text",
            "Transcription: Convert audio to text (if needed)",
            "Summarization: Extract key points",
            "Translation: Convert to Kanglish output"
        ]
        
        for i, step in enumerate(steps, 1):
            with st.container():
                st.markdown(f'<div class="success-box">', unsafe_allow_html=True)
                st.markdown(f"Step {i}: {step}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Demo section
        st.markdown("### Quick Demo")
        if st.button("Run Text Demo"):
            demo_text = "Artificial intelligence is transforming education worldwide. New technologies help students learn better and teachers teach more effectively. Key developments include personalized learning systems, automated assessment tools, and virtual classroom environments. However, challenges remain in ensuring equal access to these technologies and protecting student data privacy."
            
            st.session_state.input_type = "text"
            st.session_state.input_text = demo_text
            st.session_state.processing_complete = True
            
            with st.spinner("Processing demo text..."):
                st.session_state.transcription = demo_text
                st.session_state.summary = summarize_text(demo_text)
                st.session_state.kanglish_text = translate_to_kanglish_with_llm(st.session_state.summary)
            
            st.success("Demo processed! Go to Processing Results to view.")
            st.rerun()

def show_input_page():
    """Display content input interface with multiple options"""
    
    st.markdown('<h2 class="section-header">Input Content</h2>', unsafe_allow_html=True)
    
    # Input type selection
    input_type = st.radio(
        "Select input type:",
        ["File Upload", "YouTube URL", "Plain Text"],
        horizontal=True
    )
    
    st.markdown('<div class="input-box">', unsafe_allow_html=True)
    
    if input_type == "File Upload":
        st.subheader("Upload Audio or Video File")
        
        uploaded_file = st.file_uploader(
            "Select file",
            type=['mp3', 'wav', 'm4a', 'ogg', 'mp4', 'avi', 'mov'],
            help="Supported formats: MP3, WAV, M4A, OGG, MP4, AVI, MOV"
        )
        
        if uploaded_file is not None:
            # Display file information
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024 / 1024:.2f} MB",
                "File type": uploaded_file.type
            }
            
            st.write("File details:")
            st.json(file_details)
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{uploaded_file.name.split(".")[-1]}') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                st.session_state.audio_file_path = tmp_file.name
                st.session_state.uploaded_filename = uploaded_file.name
            
            # Process button
            if st.button("Process File Content", type="primary"):
                if 'audio_file_path' in st.session_state:
                    st.session_state.input_type = "file"
                    with st.spinner("Processing file content..."):
                        process_file_content()
                else:
                    st.error("Please upload a file first")
    
    elif input_type == "YouTube URL":
        st.subheader("YouTube Video URL")
        
        youtube_url = st.text_input(
            "Enter YouTube URL:",
            placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/...",
            help="Paste the full URL of a YouTube video"
        )
        
        if youtube_url:
            if is_youtube_url(youtube_url):
                st.success("Valid YouTube URL detected")
                video_id = extract_youtube_id(youtube_url)
                
                if video_id:
                    # Display YouTube thumbnail
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
                    st.image(thumbnail_url, width=300)
                
                if st.button("Process YouTube Video", type="primary"):
                    st.session_state.input_type = "youtube"
                    st.session_state.youtube_url = youtube_url
                    with st.spinner("Processing YouTube video..."):
                        process_youtube_content()
            else:
                st.error("Please enter a valid YouTube URL")
    
    elif input_type == "Plain Text":
        st.subheader("Enter English Text")
        
        input_text = st.text_area(
            "Paste or type English text:",
            height=200,
            placeholder="Enter the English text you want to convert to Kanglish summary...",
            help="Direct text input for quick processing without audio"
        )
        
        if st.button("Process Text Content", type="primary") and input_text.strip():
            st.session_state.input_type = "text"
            st.session_state.input_text = input_text
            with st.spinner("Processing text content..."):
                process_text_content()
        elif st.button("Process Text Content", type="primary") and not input_text.strip():
            st.error("Please enter some text to process")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_processing_page():
    """Display processing results and output"""
    
    st.markdown('<h2 class="section-header">Processing Results</h2>', unsafe_allow_html=True)
    
    if not st.session_state.get('processing_complete', False):
        st.warning("No content processed yet. Please input content first.")
        return
    
    # Display input source information
    st.subheader("Input Source")
    input_type = st.session_state.get('input_type', 'unknown')
    
    if input_type == "file":
        st.write(f"**File:** {st.session_state.get('uploaded_filename', 'Unknown')}")
        if 'audio_file_path' in st.session_state:
            st.audio(st.session_state.audio_file_path)
    
    elif input_type == "youtube":
        st.write(f"**YouTube URL:** {st.session_state.get('youtube_url', 'Unknown')}")
        st.video(st.session_state.get('youtube_url', ''))
    
    elif input_type == "text":
        st.write("**Input Text:**")
        st.text_area("Original Text", st.session_state.get('input_text', ''), height=100, disabled=True)
    
    # Create tabs for processing results
    tab1, tab2, tab3 = st.tabs(["Transcription", "English Summary", "Kanglish Output"])
    
    with tab1:
        st.subheader("Transcription")
        transcription = st.session_state.get('transcription', 'No transcription available')
        
        if input_type == "text":
            st.info("Direct text input - no transcription needed")
        
        st.text_area("Transcription Text:", transcription, height=250)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download Transcription"):
                st.info("Download functionality ready for implementation")
        with col2:
            st.metric("Word Count", len(transcription.split()))
    
    with tab2:
        st.subheader("English Summary")
        summary = st.session_state.get('summary', 'No summary available')
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.write(summary)
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            original_words = len(st.session_state.get('transcription', '').split())
            st.metric("Original Words", original_words)
        with col2:
            summary_words = len(summary.split())
            st.metric("Summary Words", summary_words)
        with col3:
            if original_words > 0:
                reduction = ((original_words - summary_words) / original_words) * 100
                st.metric("Reduction", f"{reduction:.1f}%")
    
    with tab3:
        st.subheader("Kanglish Translation")
        kanglish_text = st.session_state.get('kanglish_text', 'No Kanglish translation available')
        
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.write(kanglish_text)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.info("Kanglish combines Kannada and English for natural understanding by Kannada speakers")

def show_settings_page():
    """Display application settings"""
    
    st.markdown('<h2 class="section-header">Application Settings</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Processing Preferences")
        
        content_type = st.selectbox(
            "Default Content Type:",
            ["Auto-detect", "News", "Podcast", "Educational", "Interview", "General"]
        )
        
        summary_length = st.select_slider(
            "Summary Detail Level:",
            options=["Brief", "Moderate", "Detailed"],
            value="Moderate"
        )
    
    with col2:
        st.subheader("Output Preferences")
        
        output_format = st.selectbox(
            "Primary Output Format:",
            ["Text", "Bullet Points", "Paragraph"],
            value="Paragraph"
        )
        
        translation_level = st.select_slider(
            "Translation Style:",
            options=["More Kannada", "Balanced", "More English"],
            value="Balanced"
        )
    
    # API Configuration
    st.subheader("API Configuration")

    assemblyai_api_key = st.text_input(
        "AssemblyAI API Key:",
        type="password",
        placeholder="Enter your API key for audio processing",
        value=st.session_state.get("ASSEMBLYAI_API_KEY", "")
    )
    if assemblyai_api_key:
        st.session_state["ASSEMBLYAI_API_KEY"] = assemblyai_api_key

    openrouter_api_key = st.text_input(
        "OpenRouter API Key:",
        type="password",
        placeholder="Enter your free key from OpenRouter for translation",
        value=st.session_state.get("OPENROUTER_API_KEY", "")
    )
    if openrouter_api_key:
        st.session_state["OPENROUTER_API_KEY"] = openrouter_api_key

    if st.button("Save Settings", type="primary"):
        st.session_state.settings = {
            'content_type': content_type,
            'summary_length': summary_length,
            'output_format': output_format,
            'translation_level': translation_level
        }
        st.success("Settings saved for this session")

def process_file_content():
    """Process uploaded file content"""
    if aai.settings.api_key == "YOUR_ASSEMBLYAI_API_KEY_HERE":
        st.error("AssemblyAI API key not configured. Please set it in Settings.")
        return
    
    # Step 1: Transcription
    with st.status("Transcribing file content...", expanded=True) as status:
        transcription = transcribe_audio(st.session_state.audio_file_path)
        if transcription:
            st.session_state.transcription = transcription
            status.update(label="Transcription complete", state="complete")
        else:
            status.update(label="Transcription failed", state="error")
            return
    
    # Continue with processing
    continue_processing()

def process_youtube_content():
    """Process YouTube content"""
    if aai.settings.api_key == "YOUR_ASSEMBLYAI_API_KEY_HERE":
        st.error("AssemblyAI API key not configured. Please set it in Settings.")
        return
    
    # Step 1: Transcription
    with st.status("Transcribing YouTube video...", expanded=True) as status:
        transcription = transcribe_youtube(st.session_state.youtube_url)
        if transcription:
            st.session_state.transcription = transcription
            status.update(label="Transcription complete", state="complete")
        else:
            status.update(label="Transcription failed", state="error")
            return
    
    # Continue with processing
    continue_processing()

def process_text_content():
    """Process direct text input"""
    # For text input, use the text directly as transcription
    st.session_state.transcription = st.session_state.input_text
    continue_processing()

def continue_processing():
    """Common processing steps after transcription"""
    # Step 2: Summarization
    with st.status("Summarizing content...", expanded=True) as status:
        summary = summarize_text(st.session_state.transcription)
        st.session_state.summary = summary
        status.update(label="Summarization complete", state="complete")
    
    # Step 3: Kanglish Translation
    with st.status("Translating to Kanglish...", expanded=True) as status:
        kanglish_text = translate_to_kanglish_with_llm(st.session_state.summary)
        st.session_state.kanglish_text = kanglish_text
        status.update(label="Translation complete", state="complete")
    
    # Mark processing as complete
    st.session_state.processing_complete = True
    st.success("Processing complete! View results below.")
    st.rerun()

# Initialize session state variables
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'kanglish_text' not in st.session_state:
    st.session_state.kanglish_text = ""
if 'input_type' not in st.session_state:
    st.session_state.input_type = ""

if __name__ == "__main__":
    main()