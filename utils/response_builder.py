import json
import os
from difflib import get_close_matches
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

class ResponseBuilder:
    def __init__(self, knowledge_file):
        self.knowledge_file = knowledge_file
        self.knowledge = []
        
        # Load knowledge base with error handling
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Loading knowledge file: {knowledge_file}")
                self.knowledge = json.loads(content)
                print(f"Successfully loaded {len(self.knowledge)} items from knowledge base")
        except json.JSONDecodeError as e:
            print(f"JSON Error in {knowledge_file}: {e}")
            self.knowledge = []  # Fallback to empty list
        except FileNotFoundError:
            print(f"File Not Found: {knowledge_file}")
            self.knowledge = []
        
        # Initialize OpenAI API
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("❌ Error: OPENAI_API_KEY is not set or invalid!")

    def get_response(self, question, lang='fa'):
        print(f"Processing question: {question} (language: {lang})")
        
        # Try exact match
        for item in self.knowledge:
            if 'questions' not in item or 'answers' not in item:
                print(f"Warning: Invalid item in knowledge base: {item}")
                continue
            if question.lower() in [q.lower() for q in item['questions']]:
                print(f"Found exact match in knowledge base")
                return self._format_response(item, lang)
        
        # Try close match
        all_questions = []
        for item in self.knowledge:
            if 'questions' in item:
                all_questions.extend(item['questions'])
        
        close_matches = get_close_matches(question, all_questions, n=1, cutoff=0.6)
        if close_matches:
            for item in self.knowledge:
                if 'questions' in item and close_matches[0] in item['questions']:
                    print(f"Found close match: {close_matches[0]}")
                    return self._format_response(item, lang)
        
        # Use AI fallback if no match found
        print("No match found in knowledge base, falling back to AI")
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _ai_fallback_response(self, question, lang):
        system_prompt = {
            'fa': "شما یک دستیار هوش مصنوعی هستید که به سؤالات کاربران درباره موضوعات مختلف، به‌ویژه بورسیه‌های تحصیلی، به زبان فارسی پاسخ می‌دهید. پاسخ‌ها باید دقیق، مختصر، و مفید باشند.",
            'it': "Sei un assistente AI che risponde alle domande degli utenti su vari argomenti, in particolare borse di studio, in italiano. Le risposte devono essere precise, concise e utili.",
            'en': "You are an AI assistant answering user questions on various topics, especially scholarships, in English. Responses should be accurate, concise, and helpful."
        }[lang]

        prompt = f"{system_prompt}\n\n❓ سؤال: {question}"

        try:
            print(f"Sending request to OpenAI API for question: {question}")
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # Changed to gpt-4o for ChatGPT Plus
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            ai_response = response.choices[0].message.content.strip()
            print(f"Received AI response: {ai_response}")
            
            # Save the question and AI response to knowledge base
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
        new_entry = {
            "questions": [question],
            "answers": {lang: answer}
        }
        self.knowledge.append(new_entry)
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=4)
            print(f"Successfully saved new entry to {self.knowledge_file}")
        except Exception as e:
            print(f"Error saving to knowledge base: {e}")
