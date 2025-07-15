import json
from difflib import get_close_matches

class ResponseBuilder:
    def __init__(self, knowledge_file):
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            self.knowledge = json.load(f)
    
    def get_response(self, question, lang='fa'):
        # Try to find exact match first
        for item in self.knowledge:
            if question.lower() in [q.lower() for q in item['questions']]:
                return self._format_response(item, lang)
        
        # Try to find similar questions
        all_questions = []
        for item in self.knowledge:
            all_questions.extend(item['questions'])
        
        close_matches = get_close_matches(question, all_questions, n=1, cutoff=0.6)
        if close_matches:
            for item in self.knowledge:
                if close_matches[0] in item['questions']:
                    return self._format_response(item, lang)
        
        # If no match found, return default response
        if lang == 'fa':
            return "متأسفانه پاسخی برای سوال شما یافت نشد. لطفاً سوال خود را به شکل دیگری مطرح کنید."
        elif lang == 'it':
            return "Sfortunatamente, non ho trovato una risposta alla tua domanda. Per favore, riformula la tua domanda."
        else:
            return "Unfortunately, I couldn't find an answer to your question. Please rephrase your question."
    
    def _format_response(self, item, lang):
        if lang in item['answers']:
            answer = item['answers'][lang]
        else:
            answer = item['answers']['fa']  # Default to Persian if translation not available
        
        if 'section' in item:
            if lang == 'fa':
                answer = f"طبق بند {item['section']} از فایل بورس: {answer}"
            elif lang == 'it':
                answer = f"Secondo la sezione {item['section']} del file borsa: {answer}"
            else:
                answer = f"According to section {item['section']} of the scholarship file: {answer}"
        
        return answer