import json
from difflib import get_close_matches
import openai
import os

class ResponseBuilder:
    def __init__(self, knowledge_file):
        # Load knowledge base
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            self.knowledge = json.load(f)
        
        self.knowledge_file = knowledge_file
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def get_response(self, question, lang='fa'):
        # Try exact match
        for item in self.knowledge:
            if question.lower() in [q.lower() for q in item['questions']]:
                return self._format_response(item, lang)
        
        # Try close match
        all_questions = []
        for item in self.knowledge:
            all_questions.extend(item['questions'])
        
        close_matches = get_close_matches(question, all_questions, n=1, cutoff=0.6)
        if close_matches:
            for item in self.knowledge:
                if close_matches[0] in item['questions']:
                    return self._format_response(item, lang)
        
        # Use AI fallback if no match found
        return self._ai_fallback_response(question, lang)

    def _format_response(self, item, lang):
        answer = item['answers'].get(lang, item['answers'].get('fa', ''))
        if 'section' in item:
            section_note = {
                'fa': f"طبق بند {item['section']} از فایل بورس:",
                'it': f"Secondo la sezione {item['section']} del file borsa:",
                'en': f"According to section {item['section']} of the scholarship file:"
            }.get(lang, '')
            answer = f"{section_note} {answer}"
        return answer

    def _ai_fallback_response(self, question, lang):
        # Define system prompt based on language
        system_prompt = {
            'fa': "شما یک دستیار هوش مصنوعی هستید که به سؤالات کاربران درباره موضوعات مختلف به زبان فارسی پاسخ می‌دهید. پاسخ‌ها باید دقیق، مختصر و مفید باشند.",
            'it': "Sei un assistente AI che risponde alle domande degli utenti su vari argomenti in italiano. Le risposte devono essere precise, concise e utili.",
            'en': "You are an AI assistant answering user questions on various topics in English. Responses should be accurate, concise, and helpful."
        }[lang]

        prompt = f"{system_prompt}\n\n❓ سؤال: {question}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            ai_response = response.choices[0].message.content.strip()

            # Save the question and AI response to knowledge base (optional)
            self._save_to_knowledge_base(question, ai_response, lang)

            return ai_response
        except Exception as e:
            print(f"❌ AI error: {e}")
            return {
                'fa': "خطا در پاسخ‌دهی هوش مصنوعی. لطفاً بعداً تلاش کنید.",
                'it': "Errore nel rispondere tramite AI. Riprova più tardi.",
                'en': "AI response error. Please try again later."
            }[lang]

    def _save_to_knowledge_base(self, question, answer, lang):
        # Add the new question and answer to the knowledge base
        new_entry = {
            "questions": [question],
            "answers": {lang: answer}
        }
        self.knowledge.append(new_entry)
        
        # Save updated knowledge base back to file
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, ensure_ascii=False, indent=4)
