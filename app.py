import streamlit as st
import whisper
import os
from datetime import datetime
from intelligence import LectureAnalyzer
from summarizer import LectureSummarizer

# Page configuration
st.set_page_config(
    page_title="Smart Lecture Companion",
    page_icon="🎓",
    layout="wide"
)

# Title and description
st.title("🎓 Smart Lecture Companion")
st.markdown("### AI-Powered Lecture Transcription System")
st.markdown("Upload your lecture audio or video, and get instant transcription with timestamps!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    model_size = st.selectbox(
        "Model Size",
        ["tiny", "base", "small"],
        index=1,  # Default to "base"
        help="Larger models are more accurate but slower"
    )

    st.markdown("---")
    st.markdown("### 🤖 AI Summary Settings")
    
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your free API key from console.anthropic.com"
    )
    
    enable_ai_summary = st.toggle(
        "Enable AI Summary",
        value=False,
        help="Uses Claude AI to generate meaningful summaries"
    )
    
    if not api_key and enable_ai_summary:
        st.warning("⚠️ Please enter API key to use AI Summary")
    
    st.info("""
    **Model Comparison:**
    - **Tiny:** Fastest, ~80% accuracy
    - **Base:** Balanced (recommended)
    - **Small:** More accurate, slower
    """)
    
    st.markdown("---")
    st.markdown("**About:**")
    st.markdown("Built by Mency Christian")
    st.markdown("MACS Project - Dalhousie University")

# Main content
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader(
    "📤 Upload Audio or Video File",
    type=['mp3', 'wav', 'm4a', 'mp4', 'mov', 'avi', 'flac', 'ogg'],
    help="Supported formats: MP3, WAV, M4A, MP4, MOV, AVI, FLAC, OGG"
)

# Show uploaded file info
if uploaded_file is not None:
    # Display file info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 Filename", uploaded_file.name)
    with col2:
        st.metric("📊 Size", f"{uploaded_file.size / 1024 / 1024:.2f} MB")
    with col3:
        file_type = uploaded_file.name.split('.')[-1].upper()
        st.metric("🎵 Format", file_type)
    
    # Audio/video player
    if uploaded_file.type.startswith('audio'):
        st.audio(uploaded_file)
    elif uploaded_file.type.startswith('video'):
        st.video(uploaded_file)
    
    st.markdown("---")
    
    # Transcribe button
    if st.button("🎯 Transcribe", type="primary", use_container_width=True):
        
        # Save uploaded file temporarily
        temp_file = f"temp_{uploaded_file.name}"
        with open(temp_file, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Progress indication
        with st.spinner(f"🔄 Loading {model_size} model..."):
            model = whisper.load_model(model_size)
        
        st.success("✅ Model loaded!")
        
        # Transcription with progress bar
        with st.spinner("🎤 Transcribing... This may take 1-2 minutes..."):
            result = model.transcribe(temp_file)
        
        # Clean up temp file
        os.remove(temp_file)
        
        st.success("✅ Transcription complete!")
        
        # Basic Analysis
        with st.spinner("🧠 Analyzing content..."):
            analyzer = LectureAnalyzer()
            summary = analyzer.generate_summary(result['segments'])
            summary_text = analyzer.format_summary_text(summary)
        st.success("✅ Basic analysis complete!")
        
       # AI Summary (if enabled)
        ai_summary = None
        if enable_ai_summary and api_key:
            try:
                with st.spinner("🤖 Generating AI summary... (30-60 seconds)"):
                    summarizer = LectureSummarizer(api_key)
                    ai_summary = summarizer.generate_report_summary(result['segments'])
                    
                    if ai_summary.get('success'):
                        st.success("✅ AI Summary generated!")
                    else:
                        st.error(f"AI Summary failed: {ai_summary.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"AI Summary error: {str(e)}")
                ai_summary = {'success': False, 'error': str(e)}
        
        # Store everything
        st.session_state['result'] = result
        st.session_state['summary'] = summary
        st.session_state['summary_text'] = summary_text
        st.session_state['ai_summary'] = ai_summary
        st.session_state['transcription_done'] = True

# Display results if available
if 'transcription_done' in st.session_state and st.session_state['transcription_done']:
    result = st.session_state['result']
    
    st.markdown("---")
    st.header("📝 Results")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Full Text", 
        "⏱️ Timestamped",
        "📚 Summary",
        "🔍 Search",
        "📊 Info"
    ])
    
    # Tab 1: Full transcription
    with tab1:
        st.subheader("Full Transcription")
        
        full_text = result["text"]
        st.text_area(
            "Transcription",
            full_text,
            height=400,
            label_visibility="collapsed"
        )
        
        # Download button
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 Download Transcription",
            data=full_text,
            file_name=f"transcription_{timestamp}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Tab 2: Timestamped segments
    with tab2:
        st.subheader("Timestamped Segments")
        
        for i, segment in enumerate(result["segments"]):
            start_min = int(segment['start'] // 60)
            start_sec = int(segment['start'] % 60)
            end_min = int(segment['end'] // 60)
            end_sec = int(segment['end'] % 60)
            
            time_str = f"{start_min}:{start_sec:02d} - {end_min}:{end_sec:02d}"
            
            with st.expander(f"⏱️ [{time_str}] {segment['text'][:60]}..."):
                st.write(segment['text'])
                st.caption(f"Start: {segment['start']:.2f}s | End: {segment['end']:.2f}s")
    
    # Tab 3: Summary
    with tab3:
        # Check if AI summary exists
        ai_summary = st.session_state.get('ai_summary', None)
        
        if ai_summary and 'error' not in ai_summary:
            # ═══════════════════════════════════════
            # AI-POWERED SUMMARY (Rich Report Format)
            # ═══════════════════════════════════════
            
            st.markdown(f"# 🎓 {ai_summary.get('lecture_title', 'Lecture Summary')}")
            
            # Overview
            overview = ai_summary.get('overview', '')
            if overview:
                st.info(f"📋 **Overview:** {overview}")
            
            # Statistics
            topics = ai_summary.get('topics', [])
            if topics:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📌 Topics", len(topics))
                with col2:
                    total_terms = sum(len(t.get('key_terms', [])) for t in topics)
                    st.metric("📖 Key Terms", total_terms)
                with col3:
                    total_points = sum(len(t.get('key_points', [])) for t in topics)
                    st.metric("🎯 Key Points", total_points)
                
                st.markdown("---")
                
                # Topic-by-topic breakdown
                for i, topic in enumerate(topics, 1):
                    st.markdown(f"## 📌 Topic {i}: {topic.get('title', 'Unknown')}")
                    
                    # Time range
                    start_time = topic.get('start_time', '')
                    end_time = topic.get('end_time', '')
                    if start_time and end_time:
                        st.caption(f"⏱️ Time: {start_time} - {end_time}")
                    
                    # What was covered
                    summary_text = topic.get('summary', '')
                    if summary_text:
                        st.markdown("**📝 What was covered:**")
                        st.write(summary_text)
                    
                    # Key points
                    key_points = topic.get('key_points', [])
                    if key_points:
                        st.markdown("**🎯 Key Points:**")
                        for point in key_points:
                            st.markdown(f"• {point}")
                    
                    # Key terms with definitions
                    key_terms = topic.get('key_terms', [])
                    if key_terms:
                        st.markdown("**📖 Key Terms:**")
                        for term_obj in key_terms:
                            term = term_obj.get('term', '')
                            definition = term_obj.get('definition', '')
                            if term and definition:
                                st.markdown(
                                    f"<div style='background:#f0f7ff; padding:10px; "
                                    f"margin:8px 0; border-radius:5px; "
                                    f"border-left:4px solid #0066cc;'>"
                                    f"<strong>{term}:</strong> {definition}</div>",
                                    unsafe_allow_html=True
                                )
                    
                    st.markdown("---")
                
                # Conclusion
                conclusion = ai_summary.get('conclusion', '')
                if conclusion:
                    st.markdown("## 🏁 Conclusion")
                    st.success(conclusion)
                
                # Study tips
                study_tips = ai_summary.get('study_tips', [])
                if study_tips:
                    st.markdown("## 💡 Study Tips")
                    for tip in study_tips:
                        st.markdown(f"✅ {tip}")
                
                st.markdown("---")
                
                # Download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Format for download
                download_text = f"# {ai_summary.get('lecture_title', 'Lecture Summary')}\n\n"
                download_text += f"## Overview\n{overview}\n\n"
                
                for i, topic in enumerate(topics, 1):
                    download_text += f"## {i}. {topic.get('title', '')}\n"
                    download_text += f"**Time:** [{topic.get('start_time', '')} - {topic.get('end_time', '')}]\n\n"
                    download_text += f"{topic.get('summary', '')}\n\n"
                    
                    if topic.get('key_points'):
                        download_text += "**Key Points:**\n"
                        for point in topic['key_points']:
                            download_text += f"- {point}\n"
                        download_text += "\n"
                    
                    if topic.get('key_terms'):
                        download_text += "**Key Terms:**\n"
                        for term_obj in topic['key_terms']:
                            download_text += f"- **{term_obj.get('term', '')}**: {term_obj.get('definition', '')}\n"
                        download_text += "\n"
                    
                    download_text += "---\n\n"
                
                if conclusion:
                    download_text += f"## Conclusion\n{conclusion}\n\n"
                
                if study_tips:
                    download_text += "## Study Tips\n"
                    for tip in study_tips:
                        download_text += f"- {tip}\n"
                
                st.download_button(
                    label="📥 Download AI Summary",
                    data=download_text,
                    file_name=f"lecture_summary_{timestamp}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            else:
                st.warning("AI summary generated but no topics found. Try with a longer lecture.")
        
        else:
            # ═══════════════════════════════════════
            # FALLBACK: Basic Summary or Instructions
            # ═══════════════════════════════════════
            
            if not st.session_state.get('ai_summary'):
                st.info("""
                💡 **AI Summary Not Enabled**
                
                To get a detailed, report-style summary:
                1. Add your Anthropic API key in the sidebar
                2. Enable "AI Summary" toggle
                3. Transcribe your lecture
                
                You'll get:
                - Topic-by-topic breakdown with timestamps
                - Plain English explanations of what was taught
                - Key terms with clear definitions
                - Study tips tailored to the content
                
                Get a free API key at: https://console.anthropic.com/
                """)
            
            # Show basic summary as fallback
            summary = st.session_state.get('summary', {})
            
            if summary:
                st.markdown("### 📊 Basic Analysis")
                st.caption("(Enable AI Summary for better results)")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🎯 Important Segments", len(summary.get('key_points', [])))
                with col2:
                    st.metric("📖 Definitions", len(summary.get('definitions', [])))
                with col3:
                    st.metric("🏷️ Topics", len(summary.get('key_topics', [])))
                
                # Show a few important segments
                key_points = summary.get('key_points', [])
                if key_points:
                    st.markdown("---")
                    st.markdown("**Important Segments:**")
                    for i, point in enumerate(key_points[:5], 1):
                        time_min = int(point['start'] // 60)
                        time_sec = int(point['start'] % 60)
                        st.markdown(f"{i}. [{time_min}:{time_sec:02d}] {point['text'][:100]}...")
    
    # Tab 4: Search functionality
    with tab4:
        st.subheader("🔍 Search Transcription")
        
        search_query = st.text_input(
            "Enter search term:",
            placeholder="e.g., recursion, algorithm, neural network"
        )
        
        if search_query:
            matching_segments = []
            
            for segment in result["segments"]:
                if search_query.lower() in segment["text"].lower():
                    matching_segments.append(segment)
            
            if matching_segments:
                st.success(f"✅ Found {len(matching_segments)} matches for '{search_query}'")
                
                for segment in matching_segments:
                    start_min = int(segment['start'] // 60)
                    start_sec = int(segment['start'] % 60)
                    time_str = f"{start_min}:{start_sec:02d}"
                    
                    # Highlight the search term
                    text = segment['text']
                    highlighted_text = text.replace(
                        search_query,
                        f"**{search_query}**"
                    )
                    
                    st.info(f"**[{time_str}]** {highlighted_text}")
            else:
                st.warning(f"No matches found for '{search_query}'")
    
    # Tab 5: Transcription info
    with tab5:
        st.subheader("📊 Transcription Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🌍 Detected Language", result['language'].upper())
            st.metric("📝 Total Segments", len(result['segments']))
            
            # Calculate total duration
            total_duration = result['segments'][-1]['end']
            minutes = int(total_duration // 60)
            seconds = int(total_duration % 60)
            st.metric("⏱️ Duration", f"{minutes}m {seconds}s")
        
        with col2:
            # Word count
            word_count = len(result['text'].split())
            st.metric("📊 Word Count", word_count)
            
            # Speaking rate
            words_per_minute = int(word_count / (total_duration / 60))
            st.metric("🗣️ Speaking Rate", f"{words_per_minute} WPM")
            
            # Average segment length
            avg_segment = total_duration / len(result['segments'])
            st.metric("📏 Avg Segment", f"{avg_segment:.1f}s")

else:
    # Instructions when no file uploaded
    st.info("""
    ### 👆 Get Started
    
    1. **Upload** an audio or video file using the file uploader above
    2. **Choose** model size in the sidebar (Base recommended)
    3. **Click** the Transcribe button
    4. **View** your results in organized tabs!
    
    ### ✨ Features
    
    - 🎤 Transcribe lectures, meetings, recordings
    - ⏱️ Automatic timestamps for every segment
    - 🔍 Search through transcription
    - 📥 Download results as text file
    - 🌍 Supports 99+ languages
    - 🎥 Works with audio AND video files
    
    ### 📝 Supported Formats
    
    **Audio:** MP3, WAV, M4A, FLAC, OGG  
    **Video:** MP4, MOV, AVI
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Smart Lecture Companion v1.0 | Built with Streamlit & OpenAI Whisper</p>
        <p>MACS Project 2026 - Dalhousie University</p>
    </div>
    """,
    unsafe_allow_html=True
)