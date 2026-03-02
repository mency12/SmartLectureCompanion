import re
from collections import Counter

class LectureAnalyzer:
    """
    Analyzes lecture transcriptions to identify important content
    """
    
    def __init__(self):
        # Words that indicate importance
        self.emphasis_markers = [
            "important", "key", "remember", "note that", "critical",
            "essential", "main point", "crucial", "significant",
            "pay attention", "this will be on the exam", "make sure",
            "don't forget", "keep in mind", "take note", "focus on"
        ]
        
        # FIXED: Better definition patterns
        self.definition_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:is|means|refers to|is defined as|can be defined as)\s+',
            r'\b([a-z]+)\s+(?:is when|means that|refers to when)\s+',
        ]
    
    def detect_important_segments(self, segments):
        """Identify segments that contain important information"""
        important = []
        
        for segment in segments:
            text = segment['text']
            text_lower = text.lower()
            score = 0
            reasons = []
            
            # Check for emphasis markers
            for marker in self.emphasis_markers:
                if marker in text_lower:
                    score += 3
                    reasons.append(f"Emphasis: '{marker}'")
            
            # Check for definitions (improved)
            for pattern in self.definition_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Only count if the matched term is substantial (not "first", "which", etc.)
                    for match in matches:
                        if len(match) > 3 and match.lower() not in ['this', 'that', 'which', 'first', 'then']:
                            score += 2
                            reasons.append("Contains definition")
                            break
            
            # Check for questions
            if '?' in text:
                score += 1
                reasons.append("Contains question")
            
            # Check for numbers/statistics
            if re.search(r'\d+', text):
                score += 1
                reasons.append("Contains numbers/data")
            
            # Longer segments (detailed explanations)
            if len(text.split()) > 20:
                score += 1
                reasons.append("Detailed explanation")
            
            if score >= 2:
                important.append({
                    **segment,
                    'importance_score': score,
                    'reasons': reasons,
                })
        
        # Sort by importance
        important.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return important
    
    def extract_definitions(self, segments):
        """Extract REAL definitions from transcript"""
        definitions = []
        seen_terms = set()  # Avoid duplicates
        
        for segment in segments:
            text = segment['text']
            
            # Look for proper definition patterns
            patterns = [
                (r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+is\s+([^.?!]+)', 'is'),
                (r'\b([A-Z][a-zA-Z]+)\s+means\s+([^.?!]+)', 'means'),
                (r'\b([a-zA-Z]+)\s+refers to\s+([^.?!]+)', 'refers to'),
            ]
            
            for pattern, connector in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    term = match.group(1).strip()
                    definition_part = match.group(2).strip()
                    
                    # Filter out garbage
                    if (len(term) > 3 and 
                        term.lower() not in ['this', 'that', 'which', 'first', 'then', 'what', 'there'] and
                        term not in seen_terms and
                        len(definition_part) > 10):
                        
                        # Get full sentence for context
                        sentences = text.split('.')
                        for sent in sentences:
                            if term in sent:
                                definitions.append({
                                    'term': term,
                                    'definition': sent.strip(),
                                    'timestamp': segment['start']
                                })
                                seen_terms.add(term)
                                break
        
        return definitions[:10]  # Limit to 10 best definitions
    
    def extract_key_topics(self, segments):
        """Extract meaningful key topics"""
        all_text = ' '.join([seg['text'] for seg in segments])
        
        # Find capitalized terms (likely important concepts)
        capitalized_terms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', all_text)
        
        # Count frequency
        term_freq = Counter(capitalized_terms)
        
        # Get top terms that appear multiple times
        key_topics = [
            term for term, count in term_freq.most_common(15) 
            if count >= 2 and len(term) > 3
        ]
        
        return key_topics[:10]  # Top 10
    
    def generate_summary(self, segments, max_points=10):
        """Generate a bullet-point summary"""
        important = self.detect_important_segments(segments)
        definitions = self.extract_definitions(segments)
        key_topics = self.extract_key_topics(segments)
        
        summary = {
            'key_points': important[:max_points],
            'definitions': definitions,
            'key_topics': key_topics,
            'total_segments': len(segments),
            'important_segments': len(important)
        }
        
        return summary
    
    def format_summary_text(self, summary):
        """Format summary as readable text"""
        text = "# 📚 Lecture Summary\n\n"
        
        # Key points
        text += "## 🎯 Important Points\n\n"
        if summary['key_points']:
            for i, point in enumerate(summary['key_points'], 1):
                time_min = int(point['start'] // 60)
                time_sec = int(point['start'] % 60)
                time_str = f"{time_min}:{time_sec:02d}"
                
                text += f"**{i}. [{time_str}]** {point['text']}\n"
                text += f"   *Score: {point['importance_score']} | {', '.join(point['reasons'])}*\n\n"
        
        # Definitions
        text += "## 📖 Key Definitions\n\n"
        if summary['definitions']:
            for defn in summary['definitions']:
                time_min = int(defn['timestamp'] // 60)
                time_sec = int(defn['timestamp'] % 60)
                time_str = f"{time_min}:{time_sec:02d}"
                
                text += f"**{defn['term']}** [{time_str}]\n"
                text += f"> {defn['definition']}\n\n"
        
        # Key topics
        text += "## 🏷️ Main Topics\n\n"
        if summary['key_topics']:
            text += ", ".join(summary['key_topics']) + "\n"
        
        return text