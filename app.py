import streamlit as st
import whisper
import os
import io
import zipfile
from datetime import datetime
from intelligence import LectureAnalyzer
from summarizer import LectureSummarizer

# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================

def _show_ai_disabled_message(feature_name):
    """Show a consistent message when AI is not enabled."""
    st.info(f"""
    **AI Summary Not Enabled**

    To get {feature_name}, please:
    1. Add your Gemini API key in the sidebar
    2. Enable the "AI Summary" toggle
    3. Transcribe your lecture again

    Get an API key at: https://aistudio.google.com/api-keys
    """)

def _build_notes_markdown(ai_summary):
    """Build a downloadable markdown string from the structured AI output."""
    title = ai_summary.get('lecture_title', 'Lecture Notes')
    overview = ai_summary.get('overview', '')
    topics = ai_summary.get('topics', [])
    glossary = ai_summary.get('key_terms_glossary', [])
    exam_prep = ai_summary.get('exam_prep', [])
    study_tips = ai_summary.get('study_tips', [])
    conclusion = ai_summary.get('conclusion', '')
    deep_dives = ai_summary.get('concept_deep_dives', [])

    md = f"# {title}\n\n"

    if overview:
        md += f"## Overview\n\n{overview}\n\n---\n\n"

    # Topics
    for i, topic in enumerate(topics, 1):
        md += f"## {i}. {topic.get('title', 'Topic')}"
        start_t = topic.get('start_time', '')
        end_t = topic.get('end_time', '')
        if start_t and end_t:
            md += f" [{start_t} - {end_t}]"
        md += "\n\n"

        summary_text = topic.get('summary', '')
        if summary_text:
            md += f"{summary_text}\n\n"

        key_points = topic.get('key_points', [])
        if key_points:
            md += "**Key Points:**\n\n"
            for point in key_points:
                md += f"- {point}\n"
            md += "\n"

        key_terms = topic.get('key_terms', [])
        if key_terms:
            md += "**Key Terms:**\n\n"
            for t in key_terms:
                md += f"- **{t.get('term', '')}**: {t.get('definition', '')}\n"
            md += "\n"

        concept_exp = topic.get('concept_explanation', '')
        if concept_exp:
            md += f"**Concept Explanation:**\n\n{concept_exp}\n\n"

        md += "---\n\n"

    # Glossary
    if glossary:
        md += "## Key Terms Glossary\n\n"
        for item in glossary:
            term = item.get('term', '')
            defn = item.get('definition', '')
            ts = item.get('timestamp', '')
            why = item.get('why_it_matters', '')
            md += f"**{term}**"
            if ts:
                md += f" [{ts}]"
            md += f": {defn}\n"
            if why:
                md += f"  - *Why it matters:* {why}\n"
            md += "\n"
        md += "---\n\n"

    # Concept Deep Dives
    if deep_dives:
        md += "## Concept Deep Dives\n\n"
        for dive in deep_dives:
            md += f"### {dive.get('concept', 'Concept')}\n\n"
            md += f"{dive.get('explanation', '')}\n\n"
            connections = dive.get('connections', '')
            if connections:
                md += f"**Connections:** {connections}\n\n"
            example = dive.get('example', '')
            if example:
                md += f"**Example:** {example}\n\n"
            md += "---\n\n"

    # Exam Prep
    if exam_prep:
        md += "## Exam Prep\n\n"
        for i, item in enumerate(exam_prep, 1):
            md += f"{i}. {item}\n"
        md += "\n"

    # Study Tips
    if study_tips:
        md += "## Study Tips\n\n"
        for tip in study_tips:
            md += f"- {tip}\n"
        md += "\n"

    # Conclusion
    if conclusion:
        md += f"## Conclusion\n\n{conclusion}\n"

    return md


def _build_study_package_zip(result, ai_summary, basic_summary_text):
    """
    Build a ZIP file containing:
    - Full transcription (.txt)
    - Timestamped transcript (.txt)
    - Lecture notes (.md) - from AI if available, else basic
    - Key terms (.txt) - from AI if available
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Full transcription
        zf.writestr("transcription.txt", result.get('text', ''))

        # Timestamped transcript
        timestamped = ""
        for seg in result.get('segments', []):
            start_min = int(seg['start'] // 60)
            start_sec = int(seg['start'] % 60)
            end_min = int(seg['end'] // 60)
            end_sec = int(seg['end'] % 60)
            timestamped += (
                f"[{start_min}:{start_sec:02d} - "
                f"{end_min}:{end_sec:02d}] "
                f"{seg['text'].strip()}\n"
            )
        zf.writestr("timestamped_transcript.txt", timestamped)

        # Lecture notes
        if (ai_summary and ai_summary.get('success')
                and ai_summary.get('format') == 'structured'):
            notes_md = _build_notes_markdown(ai_summary)
            zf.writestr("lecture_notes.md", notes_md)
        elif (ai_summary and ai_summary.get('success')
                and ai_summary.get('summary_text')):
            zf.writestr(
                "lecture_notes.md",
                ai_summary.get('summary_text', '')
            )
        else:
            zf.writestr("basic_analysis.md", basic_summary_text)

        # Key terms
        if (ai_summary and ai_summary.get('success')
                and ai_summary.get('key_terms_glossary')):
            terms_text = "KEY TERMS & DEFINITIONS\n"
            terms_text += "=" * 40 + "\n\n"
            for item in ai_summary['key_terms_glossary']:
                term = item.get('term', '')
                defn = item.get('definition', '')
                ts = item.get('timestamp', '')
                why = item.get('why_it_matters', '')
                terms_text += f"{term}"
                if ts:
                    terms_text += f" [{ts}]"
                terms_text += f"\n  {defn}\n"
                if why:
                    terms_text += f"  Why it matters: {why}\n"
                terms_text += "\n"
            zf.writestr("key_terms.txt", terms_text)

    zip_buffer.seek(0)
    return zip_buffer

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Smart Lecture Companion",
    page_icon="🎓",
    layout="wide"
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    model_size = st.selectbox(
        "Model Size",
        ["tiny", "base", "small"],
        index=1,
        help="Larger models are more accurate but slower"
    )

    st.markdown("---")
    st.markdown("### 🤖 AI Summary Settings")

    api_key = st.text_input(
        "Gemini API key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your API key from https://aistudio.google.com/api-keys"
    )

    enable_ai_summary = st.toggle(
        "Enable AI Summary",
        value=False,
        help="Uses Claude AI to generate comprehensive study materials"
    )

    if enable_ai_summary and not api_key:
        st.warning("⚠️ Please enter your API key to use AI Summary")
    elif enable_ai_summary and api_key:
        st.success("✅ AI Summary enabled")

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

# ---------------------------------------------------------------------------
# Title and description
# ---------------------------------------------------------------------------
st.title("🎓 Smart Lecture Companion")
st.markdown("### AI-Powered Lecture Transcription System")
st.markdown(
    "Upload your lecture audio or video, and get instant transcription "
    "with timestamps, comprehensive study notes, key terms, and concept "
    "explanations!"
)

st.markdown("---")

# ---------------------------------------------------------------------------
# File uploader
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader(
    "📤 Upload Audio or Video File",
    type=['mp3', 'wav', 'm4a', 'mp4', 'mov', 'avi', 'flac', 'ogg'],
    help="Supported formats: MP3, WAV, M4A, MP4, MOV, AVI, FLAC, OGG"
)

# ---------------------------------------------------------------------------
# Show uploaded file info and transcribe
# ---------------------------------------------------------------------------
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
    if uploaded_file.type and uploaded_file.type.startswith('audio'):
        st.audio(uploaded_file)
    elif uploaded_file.type and uploaded_file.type.startswith('video'):
        st.video(uploaded_file)

    st.markdown("---")

    # Transcribe button
    if st.button("🎯 Transcribe", type="primary", use_container_width=True):

        # Save uploaded file temporarily
        temp_file = f"temp_{uploaded_file.name}"
        with open(temp_file, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # ---------------------------------------------------------------
        # Step 1: Load Whisper model
        # ---------------------------------------------------------------
        with st.spinner(f"🔄 Loading {model_size} model..."):
            model = whisper.load_model(model_size)
        st.success("✅ Model loaded!")

        # ---------------------------------------------------------------
        # Step 2: Transcribe
        # ---------------------------------------------------------------
        with st.spinner("🎤 Transcribing... This may take a few minutes..."):
            result = model.transcribe(temp_file)

        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)

        st.success("✅ Transcription complete!")

        # ---------------------------------------------------------------
        # Step 3: Basic heuristic analysis (always runs)
        # ---------------------------------------------------------------
        with st.spinner("🧠 Analyzing content..."):
            analyzer = LectureAnalyzer()
            summary = analyzer.generate_summary(result['segments'])
            summary_text = analyzer.format_summary_text(summary)
        st.success("✅ Basic analysis complete!")

        # ---------------------------------------------------------------
        # Step 4: AI Summary (if enabled and API key provided)
        # ---------------------------------------------------------------
        ai_summary = None
        if enable_ai_summary and api_key:
            try:
                with st.spinner(
                    "🤖 Generating AI study materials... "
                    "(this takes 30-90 seconds for detailed output)"
                ):
                    summarizer = LectureSummarizer(api_key)
                    ai_summary = summarizer.generate_report_summary(
                        result['segments']
                    )

                    if ai_summary.get('success'):
                        st.success("✅ AI study materials generated!")
                    else:
                        st.error(
                            f"AI Summary failed: "
                            f"{ai_summary.get('error', 'Unknown error')}"
                        )
            except Exception as e:
                st.error(f"AI Summary error: {str(e)}")
                ai_summary = {'success': False, 'error': str(e)}

        # ---------------------------------------------------------------
        # Store everything in session state
        # ---------------------------------------------------------------
        st.session_state['result'] = result
        st.session_state['summary'] = summary
        st.session_state['summary_text'] = summary_text
        st.session_state['ai_summary'] = ai_summary
        st.session_state['transcription_done'] = True


# ===========================================================================
# DISPLAY RESULTS
# ===========================================================================
if st.session_state.get('transcription_done'):
    result = st.session_state['result']
    ai_summary = st.session_state.get('ai_summary')

    st.markdown("---")
    st.header("📝 Results")

    # Check if AI summary has structured data
    has_structured_ai = (
        ai_summary
        and ai_summary.get('success')
        and ai_summary.get('format') == 'structured'
    )

    has_markdown_fallback = (
        ai_summary
        and ai_summary.get('success')
        and ai_summary.get('format') == 'markdown_fallback'
    )

    # -------------------------------------------------------------------
    # Create tabs
    # -------------------------------------------------------------------
    tab_names = [
        "📄 Full Text",
        "⏱️ Timestamped",
        "📚 Lecture Notes",
        "📖 Key Terms",
        "💡 Concepts",
        "📊 Summary & Exam Prep",
        "🔍 Search",
        "ℹ️ Info"
    ]

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(tab_names)

    # ===================================================================
    # Tab 1: Full Text
    # ===================================================================
    with tab1:
        st.subheader("Full Transcription")

        full_text = result["text"]
        st.text_area(
            "Transcription",
            full_text,
            height=400,
            label_visibility="collapsed"
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 Download Transcription",
            data=full_text,
            file_name=f"transcription_{timestamp}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # ===================================================================
    # Tab 2: Timestamped Segments
    # ===================================================================
    with tab2:
        st.subheader("Timestamped Segments")

        for i, segment in enumerate(result["segments"]):
            start_min = int(segment['start'] // 60)
            start_sec = int(segment['start'] % 60)
            end_min = int(segment['end'] // 60)
            end_sec = int(segment['end'] % 60)

            time_str = (
                f"{start_min}:{start_sec:02d} - {end_min}:{end_sec:02d}"
            )

            with st.expander(
                f"⏱️ [{time_str}] {segment['text'][:80]}..."
            ):
                st.write(segment['text'])
                st.caption(
                    f"Start: {segment['start']:.2f}s | "
                    f"End: {segment['end']:.2f}s"
                )

    # ===================================================================
    # Tab 3: Lecture Notes (NEW - comprehensive AI-generated study notes)
    # ===================================================================
    with tab3:
        st.subheader("Comprehensive Lecture Notes")

        if has_structured_ai:
            # ----- Structured AI output -----
            title = ai_summary.get('lecture_title', 'Lecture Notes')
            overview = ai_summary.get('overview', '')
            topics = ai_summary.get('topics', [])

            st.markdown(f"# {title}")

            if overview:
                st.info(f"**Overview:** {overview}")

            # Topic-by-topic detailed notes
            for i, topic in enumerate(topics, 1):
                st.markdown(f"## {i}. {topic.get('title', 'Topic')}")

                # Time range
                start_t = topic.get('start_time', '')
                end_t = topic.get('end_time', '')
                if start_t and end_t:
                    st.caption(f"⏱️ {start_t} - {end_t}")

                # Detailed summary / explanation
                summary_text = topic.get('summary', '')
                if summary_text:
                    st.markdown(summary_text)

                # Key points
                key_points = topic.get('key_points', [])
                if key_points:
                    st.markdown("**Key Points:**")
                    for point in key_points:
                        st.markdown(f"- {point}")

                st.markdown("---")

            # Conclusion
            conclusion = ai_summary.get('conclusion', '')
            if conclusion:
                st.markdown("## Conclusion")
                st.success(conclusion)

            # Download lecture notes as markdown
            download_md = _build_notes_markdown(ai_summary)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Download Lecture Notes (.md)",
                data=download_md,
                file_name=f"lecture_notes_{timestamp}.md",
                mime="text/markdown",
                use_container_width=True
            )

        elif has_markdown_fallback:
            # ----- Markdown fallback -----
            st.markdown(ai_summary.get('summary_text', ''))

        else:
            # ----- No AI -----
            _show_ai_disabled_message("lecture notes")

            # Show basic analysis as fallback
            basic_summary = st.session_state.get('summary', {})
            if basic_summary:
                st.markdown("### Basic Analysis (Heuristic)")
                st.caption("Enable AI Summary for comprehensive notes.")

                key_points = basic_summary.get('key_points', [])
                if key_points:
                    st.markdown("**Important Segments:**")
                    for i, point in enumerate(key_points[:8], 1):
                        time_min = int(point['start'] // 60)
                        time_sec = int(point['start'] % 60)
                        st.markdown(
                            f"{i}. **[{time_min}:{time_sec:02d}]** "
                            f"{point['text'][:150]}..."
                        )

    # ===================================================================
    # Tab 4: Key Terms & Definitions (NEW)
    # ===================================================================
    with tab4:
        st.subheader("Key Terms & Definitions")

        if has_structured_ai:
            glossary = ai_summary.get('key_terms_glossary', [])

            # Also collect terms from individual topics
            topic_terms = []
            for topic in ai_summary.get('topics', []):
                for term_obj in topic.get('key_terms', []):
                    topic_terms.append(term_obj)

            # Show glossary first
            if glossary:
                st.markdown("### Complete Glossary")
                for item in glossary:
                    term = item.get('term', '')
                    defn = item.get('definition', '')
                    ts = item.get('timestamp', '')
                    why = item.get('why_it_matters', '')

                    st.markdown(
                        f"<div style='background: #f0f7ff; padding: 12px; "
                        f"margin: 8px 0; border-radius: 8px; "
                        f"border-left: 4px solid #0066cc;'>"
                        f"<strong style='font-size: 1.1em;'>{term}</strong>"
                        f"{f' <span style=\"color: #666;\">[{ts}]</span>' if ts else ''}"
                        f"<br/>{defn}"
                        f"{f'<br/><em style=\"color: #555;\">Why it matters: {why}</em>' if why else ''}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            # Show per-topic terms if they add anything
            if topic_terms:
                st.markdown("### Terms by Topic")
                for topic in ai_summary.get('topics', []):
                    t_terms = topic.get('key_terms', [])
                    if t_terms:
                        st.markdown(
                            f"**{topic.get('title', 'Topic')}:**"
                        )
                        for t in t_terms:
                            st.markdown(
                                f"- **{t.get('term', '')}**: "
                                f"{t.get('definition', '')}"
                            )
                        st.markdown("")

            if not glossary and not topic_terms:
                st.warning("No key terms were identified in this lecture.")

        elif has_markdown_fallback:
            st.markdown(ai_summary.get('summary_text', ''))

        else:
            _show_ai_disabled_message("key terms")

            # Fallback: show heuristic definitions
            basic_summary = st.session_state.get('summary', {})
            definitions = basic_summary.get('definitions', [])
            if definitions:
                st.markdown("### Detected Definitions (Basic Analysis)")
                for defn in definitions:
                    time_min = int(defn['timestamp'] // 60)
                    time_sec = int(defn['timestamp'] % 60)
                    st.markdown(
                        f"- **{defn['term']}** [{time_min}:{time_sec:02d}]: "
                        f"{defn['definition']}"
                    )

    # ===================================================================
    # Tab 5: Concept Explanations (NEW)
    # ===================================================================
    with tab5:
        st.subheader("Concept Explanations")

        if has_structured_ai:
            deep_dives = ai_summary.get('concept_deep_dives', [])

            if deep_dives:
                st.markdown(
                    "Detailed explanations of the major concepts from "
                    "this lecture, written to help you truly understand "
                    "the material."
                )
                st.markdown("")

                for i, dive in enumerate(deep_dives, 1):
                    concept = dive.get('concept', f'Concept {i}')

                    with st.expander(
                        f"💡 {concept}", expanded=(i <= 2)
                    ):
                        # Main explanation
                        explanation = dive.get('explanation', '')
                        if explanation:
                            st.markdown("**Explanation:**")
                            st.markdown(explanation)

                        # Connections to other topics
                        connections = dive.get('connections', '')
                        if connections:
                            st.markdown("**Connections:**")
                            st.markdown(connections)

                        # Concrete example
                        example = dive.get('example', '')
                        if example:
                            st.markdown("**Example:**")
                            st.info(example)

                # Also show per-topic concept explanations
                topics = ai_summary.get('topics', [])
                has_topic_explanations = any(
                    t.get('concept_explanation') for t in topics
                )
                if has_topic_explanations:
                    st.markdown("---")
                    st.markdown("### Per-Topic Explanations")
                    for topic in topics:
                        ce = topic.get('concept_explanation', '')
                        if ce:
                            st.markdown(
                                f"**{topic.get('title', 'Topic')}:**"
                            )
                            st.markdown(ce)
                            st.markdown("")
            else:
                # No deep dives but maybe topic-level explanations
                topics = ai_summary.get('topics', [])
                has_any = any(t.get('concept_explanation') for t in topics)
                if has_any:
                    for topic in topics:
                        ce = topic.get('concept_explanation', '')
                        if ce:
                            st.markdown(
                                f"### {topic.get('title', 'Topic')}"
                            )
                            st.markdown(ce)
                            st.markdown("---")
                else:
                    st.warning(
                        "No concept explanations were generated. "
                        "Try with a longer or more content-rich lecture."
                    )

        elif has_markdown_fallback:
            st.markdown(ai_summary.get('summary_text', ''))

        else:
            _show_ai_disabled_message("concept explanations")

    # ===================================================================
    # Tab 6: Summary & Exam Prep (fixed version of original tab3)
    # ===================================================================
    with tab6:
        st.subheader("Summary & Exam Prep")

        if has_structured_ai:
            # Overview
            overview = ai_summary.get('overview', '')
            if overview:
                st.info(f"**Overview:** {overview}")

            # Stats
            topics = ai_summary.get('topics', [])
            glossary = ai_summary.get('key_terms_glossary', [])
            exam_prep = ai_summary.get('exam_prep', [])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📌 Topics Covered", len(topics))
            with col2:
                st.metric("📖 Key Terms", len(glossary))
            with col3:
                st.metric(
                    "🎯 Key Points",
                    sum(len(t.get('key_points', [])) for t in topics)
                )

            st.markdown("---")

            # Exam prep
            if exam_prep:
                st.markdown("### 🎯 Exam Prep - What to Focus On")
                for i, item in enumerate(exam_prep, 1):
                    st.markdown(f"**{i}.** {item}")
                st.markdown("")

            # Study tips
            study_tips = ai_summary.get('study_tips', [])
            if study_tips:
                st.markdown("### 💡 Study Tips")
                for tip in study_tips:
                    st.markdown(f"- {tip}")
                st.markdown("")

            # Conclusion
            conclusion = ai_summary.get('conclusion', '')
            if conclusion:
                st.markdown("### Conclusion")
                st.success(conclusion)

            # Download full study package
            st.markdown("---")
            zip_buffer = _build_study_package_zip(
                result, ai_summary, st.session_state.get('summary_text', '')
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Download Full Study Package (.zip)",
                data=zip_buffer,
                file_name=f"study_package_{timestamp}.zip",
                mime="application/zip",
                use_container_width=True
            )

        elif has_markdown_fallback:
            st.markdown(ai_summary.get('summary_text', ''))

        else:
            _show_ai_disabled_message("exam prep")

            # Fallback basic summary
            basic_summary = st.session_state.get('summary', {})
            if basic_summary:
                st.markdown("### Basic Analysis")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "🎯 Important Segments",
                        len(basic_summary.get('key_points', []))
                    )
                with col2:
                    st.metric(
                        "📖 Definitions",
                        len(basic_summary.get('definitions', []))
                    )
                with col3:
                    st.metric(
                        "🏷️ Topics",
                        len(basic_summary.get('key_topics', []))
                    )

    # ===================================================================
    # Tab 7: Search
    # ===================================================================
    with tab7:
        st.subheader("🔍 Search Transcription")

        search_query = st.text_input(
            "Enter search term:",
            placeholder="e.g., recursion, algorithm, neural network"
        )

        if search_query:
            matching_segments = []
            query_lower = search_query.lower()

            for segment in result["segments"]:
                if query_lower in segment["text"].lower():
                    matching_segments.append(segment)

            if matching_segments:
                st.success(
                    f"Found {len(matching_segments)} matches "
                    f"for '{search_query}'"
                )

                for segment in matching_segments:
                    start_min = int(segment['start'] // 60)
                    start_sec = int(segment['start'] % 60)
                    time_str = f"{start_min}:{start_sec:02d}"

                    # Case-insensitive highlight
                    text = segment['text']
                    import re
                    highlighted_text = re.sub(
                        re.escape(search_query),
                        f"**{search_query}**",
                        text,
                        flags=re.IGNORECASE
                    )

                    st.info(f"**[{time_str}]** {highlighted_text}")
            else:
                st.warning(f"No matches found for '{search_query}'")

    # ===================================================================
    # Tab 8: Info
    # ===================================================================
    with tab8:
        st.subheader("📊 Transcription Information")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "🌍 Detected Language",
                result.get('language', 'unknown').upper()
            )
            st.metric("📝 Total Segments", len(result['segments']))

            # Calculate total duration
            if result['segments']:
                total_duration = result['segments'][-1]['end']
                minutes = int(total_duration // 60)
                seconds = int(total_duration % 60)
                st.metric("⏱️ Duration", f"{minutes}m {seconds}s")
            else:
                total_duration = 0

        with col2:
            word_count = len(result['text'].split())
            st.metric("📊 Word Count", word_count)

            if total_duration > 0:
                words_per_minute = int(
                    word_count / (total_duration / 60)
                )
                st.metric("🗣️ Speaking Rate", f"{words_per_minute} WPM")

                avg_segment = total_duration / max(
                    len(result['segments']), 1
                )
                st.metric("📏 Avg Segment", f"{avg_segment:.1f}s")

else:
    # -------------------------------------------------------------------
    # Instructions when no file uploaded / not yet transcribed
    # -------------------------------------------------------------------
    st.info("""
    ### 👆 Get Started

    1. **Upload** an audio or video file using the file uploader above
    2. **Choose** model size in the sidebar (Base recommended)
    3. **Enable AI Summary** in the sidebar for comprehensive study materials
    4. **Click** the Transcribe button
    5. **View** your results in organized tabs!

    ### ✨ Features

    - 🎤 Transcribe lectures, meetings, recordings
    - ⏱️ Automatic timestamps for every segment
    - 📚 AI-generated comprehensive lecture notes
    - 📖 Key terms with definitions and context
    - 💡 Deep concept explanations for revision
    - 🎯 Exam prep tips and study strategies
    - 🔍 Search through transcription
    - 📥 Download study materials as .md or .zip
    - 🌍 Supports 99+ languages
    - 🎥 Works with audio AND video files

    ### 📝 Supported Formats

    **Audio:** MP3, WAV, M4A, FLAC, OGG
    **Video:** MP4, MOV, AVI
    """)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Smart Lecture Companion v2.0 | Built with Streamlit & OpenAI Whisper</p>
        <p>MACS Project 2026 - Dalhousie University</p>
    </div>
    """,
    unsafe_allow_html=True
)
