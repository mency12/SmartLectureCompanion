import anthropic
import json

class LectureSummarizer:
    """
    Uses Claude AI to generate comprehensive study notes from lecture transcriptions
    """
    
    def __init__(self, api_key):
        """
        Initialize the summarizer with Anthropic API key
        
        Args:
            api_key: Anthropic API key for Claude access
        """
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_report_summary(self, segments):
        """
        Generate comprehensive study notes from lecture transcript
        
        Args:
            segments: List of transcript segments from Whisper
            
        Returns:
            Dictionary with success status and formatted study notes
        """
        # Format transcript with timestamps
        transcript = self._format_transcript(segments)
        
        # Calculate lecture duration
        total_duration = segments[-1]['end']
        total_minutes = int(total_duration // 60)
        
        # Create comprehensive prompt for study notes
        prompt = f"""You are creating comprehensive lecture notes for students to study from.

TRANSCRIPT:
{transcript}

Create detailed study notes following this format:

# [Lecture Title] - Lecture Notes

## Overview
[2-3 sentences explaining what this lecture covered and why it matters]

---

## 1. [First Major Topic] [Start-End time]

[2-4 sentences explaining this topic. Include the key concepts and how 
they relate to each other. Explain it as if teaching someone who wasn't 
in the lecture.]

**Key Concept: [Important Concept Name]**
[2-3 sentences explaining this concept in detail, including any specific 
terms or examples from the lecture. Include timestamp if term is defined.]

**Important Points:**
- [First key point explained in a complete sentence]
- [Second key point explained in a complete sentence]
- [Third key point explained in a complete sentence]
- [Fourth key point if relevant]

---

## 2. [Second Major Topic] [Start-End time]

[Explanation of this topic with context and connections]

**Key Concept: [Important Concept Name]**
[Detailed explanation with examples]

**Important Points:**
- [Points from this section, each fully explained]

---

[Continue for all major topics - aim for 3-7 topics total]

---

## Key Definitions

**[Term 1]** [MM:SS]: [Clear, complete definition with context about 
why it matters or how it's used]

**[Term 2]** [MM:SS]: [Full explanation of what this term means and 
its significance]

**[Term 3]** [MM:SS]: [Complete definition with practical context]

[Include 5-10 most important terms]

---

## Exam Prep - What to Focus On

✓ [First key concept explained in a complete sentence that a student 
  can understand and remember]

✓ [Second important concept with enough detail to be meaningful]

✓ [Third concept to remember with context]

✓ [Fourth critical point that connects to the main themes]

✓ [Fifth key takeaway with practical application]

[Include 5-7 most important things to remember for exams]

---

CRITICAL REQUIREMENTS:

1. EXPLANATIONS: Don't just list topics - EXPLAIN them thoroughly. 
   Students should understand the concepts from your notes alone without 
   watching the lecture.

2. CONTEXT: When introducing terms, explain WHY they matter and HOW 
   they're used, not just WHAT they are. Give context that helps 
   understanding.

3. CONNECTIONS: Show how concepts relate to each other. Help students 
   see the bigger picture.

4. COMPLETENESS: Include enough detail that a student who missed the 
   lecture can study from these notes and understand the material.

5. CLARITY: Write in simple, clear language. Avoid unnecessary jargon. 
   When technical terms are needed, explain them clearly.

6. STRUCTURE: Use the exact format shown above with headers, subheaders, 
   and bullet points for easy reading.

7. TIMESTAMPS: Include [MM:SS] timestamps with definitions and when 
   referencing specific moments in the lecture.

8. IMPORTANT POINTS: These should be substantial points, not just one-word 
   items or simple facts. Each should be a complete, meaningful thought 
   that adds to understanding.

9. DEPTH: Each topic section should have 3-5 paragraphs of explanation. 
   The "Key Concept" subsections should have 2-3 sentences each.

10. STUDY VALUE: These notes should be genuinely useful for exam 
    preparation. Include the kind of details and explanations that 
    help students answer exam questions.

Return ONLY the formatted notes, no preamble, no JSON, no extra commentary."""

        try:
            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the generated text
            summary_text = message.content[0].text
            
            return {
                'success': True,
                'summary_text': summary_text,
                'format': 'markdown'
            }
            
        except anthropic.APIError as e:
            # Handle API-specific errors
            return {
                'success': False,
                'error': f"API Error: {str(e)}",
                'summary_text': f"Failed to generate AI summary: {str(e)}"
            }
        except Exception as e:
            # Handle any other errors
            return {
                'success': False,
                'error': str(e),
                'summary_text': f"AI Summary generation failed: {str(e)}"
            }
    
    def _format_transcript(self, segments):
        """
        Format transcript segments into readable text with timestamps
        
        Args:
            segments: List of transcript segments from Whisper
            
        Returns:
            Formatted string with timestamps and text
        """
        formatted = ""
        
        for segment in segments:
            # Calculate timestamp
            start_min = int(segment['start'] // 60)
            start_sec = int(segment['start'] % 60)
            time_str = f"{start_min}:{start_sec:02d}"
            
            # Add to formatted transcript
            formatted += f"[{time_str}] {segment['text'].strip()}\n"
        
        return formatted