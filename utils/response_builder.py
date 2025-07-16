import json
from difflib import get_close_matches
import openai
import os

class ResponseBuilder:
    def __init__(self, knowledge_file, fallback_text_file=None):
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            self.knowledge = json.load(f)
        
        self.fallback_text_file = fallback_text_file
        if fallback_text_file:
            with open(fallback_text_file, 'r', encoding='utf-8') as f:
                self.fallback_text = json.load(f)

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
        if not self.fallback_text_file or not self.fallback_text:
            return {
                'fa': "متأسفانه پاسخی برای سوال شما یافت نشد. لطفاً سوال خود را به شکل دیگری مطرح کنید.",
                'it': "Sfortunatamente, non ho trovato una risposta alla tua domanda.",
                'en': "Unfortunately, I couldn't find an answer to your question."
            }.get(lang, "No answer found.")

        # Build the prompt
        full_text = self.fallback_text.get("text", "")
        system_prompt = {
            'fa': "شما یک دستیار هوش مصنوعی هستید که بر اساس اطلاعات فایل بورس به سوالات کاربران پاسخ می‌دهید.",
            'it': "Sei un assistente AI che risponde alle domande sulle borse di studio in base al file fornito.",
            'en': "You are an AI assistant answering questions about scholarships based on the provided file."
        }[lang]

        prompt = f"{system_prompt}\n\n🗂 متن بورس:\n{full_text[:3000]}\n\n❓ سوال: {question}"

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
            return response.choices[0].message.content.strip()
        except Exception as e:
            print("❌ AI error:", e)
            return {
                'fa': "خطا در پاسخ‌دهی هوش مصنوعی. لطفاً بعداً تلاش کنید.",
                'it': "Errore nel rispondere tramite AI. Riprova più tardi.",
                'en': "AI response error. Please try again later."
            }[lang]
