import google.generativeai as genai
import json
import re

class LectureSummarizer:
    def __init__(self, api_key):
        # Initialize Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_report_summary(self, segments):
        transcript = self._format_transcript(segments)
        prompt = self._build_json_prompt(transcript)

        try:
            # Gemini handles the "Thinking" and "Generating" in one call
            response = self.model.generate_content(prompt)
            parsed = self._parse_json_response(response.text)

            if parsed:
                parsed['success'] = True
                parsed['format'] = 'structured'
                return parsed
            return {'success': False, 'error': "Failed to parse JSON"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _build_json_prompt(self, transcript):
        return f"""
        Act as an expert University Tutor. Use the transcript below to create a structured study guide.
        TRANSCRIPT: {transcript}

        IMPORTANT: If a concept is mentioned, explain it deeply using your own internal knowledge 
        base—do not just summarize the professor's words.

        Return ONLY a JSON object:
        {{
          "lecture_title": "Descriptive Title",
          "overview": "Contextual summary of why this matters",
          "topics": [
            {{
              "title": "Topic Name",
              "summary": "3 paragraphs of detailed explanation including outside academic context",
              "key_points": ["Insightful point 1", "Insightful point 2"],
              "key_terms": [{{"term": "Term", "definition": "Academic definition"}}],
              "concept_explanation": "A pedagogical breakdown for a struggling student"
            }}
          ],
          "key_terms_glossary": [
            {{"term": "Term", "definition": "Full definition", "timestamp": "MM:SS", "why_it_matters": "Context"}}
          ],
          "concept_deep_dives": [
            {{"concept": "Main Idea", "explanation": "Extensive breakdown", "connections": "How it links to other fields", "example": "Real-world analogy"}}
          ],
          "exam_prep": ["What to focus on for the final"],
          "study_tips": ["Actionable strategy for this specific material"],
          "conclusion": "Final wrap-up"
        }}
        """

    def _parse_json_response(self, text):
        # Removes markdown code blocks if the AI includes them
        cleaned = re.sub(r'```json|```', '', text).strip()
        try:
            return json.loads(cleaned)
        except:
            return None

    def _format_transcript(self, segments):
        # Formats Whisper segments for the AI to read
        return "\n".join([f"[{int(s['start']//60)}:{int(s['start']%60):02d}] {s['text']}" for s in segments])

# import anthropic
# import json
# import re

# class LectureSummarizer:
#     """
#     Uses Claude AI to generate comprehensive, structured study materials
#     from lecture transcriptions. Returns structured JSON that the app
#     can render into multiple tabs (notes, key terms, concepts, etc.).
#     """

#     def __init__(self, api_key):
#         """
#         Initialize the summarizer with Anthropic API key.

#         Args:
#             api_key: Anthropic API key for Claude access
#         """
#         self.client = anthropic.Anthropic(api_key=api_key)

#     def generate_report_summary(self, segments):
#         """
#         Generate comprehensive structured study materials from lecture transcript.

#         This is the main entry point. It sends the transcript to Claude and asks
#         for a structured JSON response containing topics, key terms, concept
#         explanations, and exam prep material.

#         Args:
#             segments: List of transcript segments from Whisper.
#                       Each segment has 'start', 'end', and 'text' keys.

#         Returns:
#             Dictionary with structured lecture analysis. On success, contains
#             keys like 'lecture_title', 'overview', 'topics', 'key_terms_glossary',
#             'concept_deep_dives', 'exam_prep', 'study_tips', 'conclusion',
#             plus 'success': True. On failure, contains 'success': False and
#             'error' with a message, plus 'summary_text' as a fallback.
#         """
#         # Format transcript with timestamps
#         transcript = self._format_transcript(segments)

#         # Calculate lecture duration for context
#         total_duration = segments[-1]['end'] if segments else 0
#         total_minutes = int(total_duration // 60)

#         # Build the prompt that requests structured JSON output
#         prompt = self._build_json_prompt(transcript, total_minutes)

#         try:
#             # Call Claude API with higher token limit for detailed output
#             message = self.client.messages.create(
#                 model="claude-sonnet-4-20250514",
#                 max_tokens=8000,
#                 messages=[
#                     {"role": "user", "content": prompt}
#                 ]
#             )

#             # Extract the generated text
#             raw_text = message.content[0].text

#             # Attempt to parse JSON from Claude's response
#             parsed = self._parse_json_response(raw_text)

#             if parsed is not None:
#                 # Successfully parsed structured JSON
#                 parsed['success'] = True
#                 parsed['format'] = 'structured'
#                 return parsed
#             else:
#                 # JSON parsing failed - fall back to raw markdown
#                 # This ensures the app never crashes even if Claude
#                 # doesn't return valid JSON
#                 return {
#                     'success': True,
#                     'format': 'markdown_fallback',
#                     'summary_text': raw_text,
#                     'lecture_title': 'Lecture Summary',
#                     'overview': '',
#                     'topics': [],
#                     'key_terms_glossary': [],
#                     'concept_deep_dives': [],
#                     'exam_prep': [],
#                     'study_tips': [],
#                     'conclusion': ''
#                 }

#         except anthropic.APIError as e:
#             return {
#                 'success': False,
#                 'error': f"API Error: {str(e)}",
#                 'summary_text': f"Failed to generate AI summary: {str(e)}"
#             }
#         except Exception as e:
#             return {
#                 'success': False,
#                 'error': str(e),
#                 'summary_text': f"AI Summary generation failed: {str(e)}"
#             }

#     def generate_lecture_notes_markdown(self, segments):
#         """
#         Generate comprehensive lecture notes as downloadable markdown.

#         This is a separate method that produces a nicely formatted markdown
#         document suitable for downloading and printing. Unlike the main
#         generate_report_summary which returns JSON for the UI, this returns
#         a human-readable markdown string.

#         Args:
#             segments: List of transcript segments from Whisper.

#         Returns:
#             Dictionary with 'success' and 'notes_markdown' keys.
#         """
#         transcript = self._format_transcript(segments)
#         total_duration = segments[-1]['end'] if segments else 0
#         total_minutes = int(total_duration // 60)

#         prompt = f"""You are creating comprehensive lecture notes for a university student.
# These notes should be detailed enough that a student who missed the lecture can
# study from them and fully understand the material.

# LECTURE TRANSCRIPT ({total_minutes} minutes):
# {transcript}

# Write detailed, well-organized lecture notes in Markdown format. Include:

# 1. A clear title and overview
# 2. Topic-by-topic breakdown with timestamps [MM:SS]
# 3. Thorough explanations of each concept (not just bullet points)
# 4. Key terms bolded with definitions inline
# 5. Important formulas, examples, or processes described step by step
# 6. Connections between topics
# 7. A "Key Takeaways" section at the end
# 8. An "Exam Prep" section with what to focus on

# Write as if you are a top student sharing your notes with a classmate.
# Be thorough, clear, and educational. Use proper markdown formatting.

# Return ONLY the markdown notes, no preamble or commentary."""

#         try:
#             message = self.client.messages.create(
#                 model="claude-sonnet-4-20250514",
#                 max_tokens=8000,
#                 messages=[
#                     {"role": "user", "content": prompt}
#                 ]
#             )

#             notes_text = message.content[0].text

#             return {
#                 'success': True,
#                 'notes_markdown': notes_text
#             }

#         except Exception as e:
#             return {
#                 'success': False,
#                 'error': str(e),
#                 'notes_markdown': f"Failed to generate lecture notes: {str(e)}"
#             }

#     def _build_json_prompt(self, transcript, total_minutes):
#         """
#         Build the Claude prompt that requests structured JSON output.

#         The prompt is carefully crafted to:
#         1. Ask for valid JSON wrapped in ```json``` code blocks
#         2. Provide a clear schema for Claude to follow
#         3. Include instructions for thorough educational content
#         4. Handle edge cases (short lectures, unclear content)

#         Args:
#             transcript: Formatted transcript string with timestamps.
#             total_minutes: Total lecture duration in minutes.

#         Returns:
#             The prompt string to send to Claude.
#         """
#         return f"""You are an expert educational AI assistant. Analyze this lecture transcript and produce comprehensive study materials.

# LECTURE TRANSCRIPT ({total_minutes} minutes):
# {transcript}

# Return your analysis as a JSON object wrapped in ```json``` code fences. Follow this exact schema:

# ```json
# {{
#   "lecture_title": "A descriptive title for this lecture",
#   "overview": "2-4 sentences explaining what this lecture covered, its main themes, and why it matters.",
#   "topics": [
#     {{
#       "title": "Name of the first major topic",
#       "start_time": "MM:SS",
#       "end_time": "MM:SS",
#       "summary": "3-5 paragraphs thoroughly explaining what was taught about this topic. Write as if you are teaching someone who missed the lecture. Include context, reasoning, and connections. This should be detailed enough to study from.",
#       "key_points": [
#         "First important point - a complete sentence that captures a key idea",
#         "Second important point with enough detail to be meaningful",
#         "Third point connecting this topic to the broader lecture"
#       ],
#       "key_terms": [
#         {{
#           "term": "Important Term",
#           "definition": "Clear, complete definition with context about why it matters and how it is used. 2-3 sentences."
#         }}
#       ],
#       "concept_explanation": "A detailed, tutorial-style explanation of the core concept in this topic. Write 2-3 paragraphs as if tutoring a student one-on-one. Include examples or analogies where helpful."
#     }}
#   ],
#   "key_terms_glossary": [
#     {{
#       "term": "Term Name",
#       "definition": "Complete definition with context.",
#       "timestamp": "MM:SS when this term was first mentioned or defined",
#       "why_it_matters": "1-2 sentences explaining the significance of this term in the broader context of the course."
#     }}
#   ],
#   "concept_deep_dives": [
#     {{
#       "concept": "Name of a major concept from the lecture",
#       "explanation": "3-4 paragraphs providing a thorough explanation of this concept. Go beyond what was said in the lecture - explain the underlying principles, give examples, and help the student truly understand.",
#       "connections": "How this concept connects to other topics in the lecture or the broader field.",
#       "example": "A concrete example or analogy that illustrates this concept clearly."
#     }}
#   ],
#   "exam_prep": [
#     "First thing to focus on for exams - a complete, meaningful statement",
#     "Second key concept to remember with enough context to be useful",
#     "Third important point that a student should be able to explain"
#   ],
#   "study_tips": [
#     "Specific, actionable study tip related to this lecture's content",
#     "Another study strategy tailored to the material covered"
#   ],
#   "conclusion": "2-3 sentences wrapping up the lecture's main message and how it fits into the bigger picture."
# }}
# ```

# CRITICAL REQUIREMENTS:

# 1. RETURN VALID JSON: Your response must be a single JSON object wrapped in ```json``` fences. No text before or after the JSON block.

# 2. THOROUGHNESS: The 'summary' field for each topic should be 3-5 paragraphs. The 'concept_explanation' should be 2-3 paragraphs. Students should be able to study from these notes alone.

# 3. EXPLANATIONS OVER LISTS: Don't just list facts. Explain concepts in detail with context, reasoning, and connections. Write as an excellent tutor would teach.

# 4. KEY TERMS: Include 5-15 terms in the glossary depending on lecture length. Each definition should be 2-3 sentences with context.

# 5. CONCEPT DEEP DIVES: Include 2-5 deep dives on the most important concepts. These should go beyond surface-level summaries.

# 6. TIMESTAMPS: Use [MM:SS] format. Reference the actual timestamps from the transcript.

# 7. TOPICS: Identify 3-7 major topics depending on lecture length and content density.

# 8. EXAM PREP: Include 5-8 specific, actionable items. Not vague suggestions but concrete concepts a student should understand.

# 9. ACCURACY: Base everything on the actual transcript content. Do not invent information not present in the lecture.

# 10. STUDY VALUE: Every section should provide genuine educational value for exam preparation."""

#     def _parse_json_response(self, raw_text):
#         """
#         Parse JSON from Claude's response.

#         Claude typically wraps JSON in ```json``` code fences. This method
#         handles multiple formats:
#         1. JSON inside ```json ... ``` code fences
#         2. JSON inside ``` ... ``` code fences (no language specified)
#         3. Raw JSON without code fences

#         Args:
#             raw_text: The raw text response from Claude.

#         Returns:
#             Parsed dictionary if successful, None if parsing fails.
#         """
#         # Strategy 1: Extract from ```json ... ``` code fence
#         json_match = re.search(r'```json\s*\n?(.*?)\n?\s*```', raw_text, re.DOTALL)
#         if json_match:
#             try:
#                 return json.loads(json_match.group(1))
#             except json.JSONDecodeError:
#                 pass

#         # Strategy 2: Extract from ``` ... ``` code fence (any language)
#         code_match = re.search(r'```\s*\n?(.*?)\n?\s*```', raw_text, re.DOTALL)
#         if code_match:
#             try:
#                 return json.loads(code_match.group(1))
#             except json.JSONDecodeError:
#                 pass

#         # Strategy 3: Try parsing the entire response as JSON
#         try:
#             return json.loads(raw_text)
#         except json.JSONDecodeError:
#             pass

#         # Strategy 4: Try to find a JSON object in the text (starts with { ends with })
#         brace_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
#         if brace_match:
#             try:
#                 return json.loads(brace_match.group(0))
#             except json.JSONDecodeError:
#                 pass

#         # All strategies failed
#         return None

#     def _format_transcript(self, segments):
#         """
#         Format transcript segments into readable text with timestamps.

#         Args:
#             segments: List of transcript segments from Whisper.

#         Returns:
#             Formatted string with [MM:SS] timestamps and text.
#         """
#         formatted = ""

#         for segment in segments:
#             start_min = int(segment['start'] // 60)
#             start_sec = int(segment['start'] % 60)
#             time_str = f"{start_min}:{start_sec:02d}"

#             formatted += f"[{time_str}] {segment['text'].strip()}\n"

#         return formatted
