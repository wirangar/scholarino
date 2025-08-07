import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class GoogleSheetsClient:
    def __init__(self, config):
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config['credentials_file'], scope)
        client = gspread.authorize(creds)

        # ✅ باز کردن شیت با استفاده از sheet_id نه نام
        self.sheet = client.open_by_key(config['sheet_id'])

        # ✅ استفاده از worksheet_name و questions_worksheet
        self.users_worksheet = self.sheet.worksheet(config['worksheet_name'])
        self.questions_worksheet = self.sheet.worksheet(config['questions_worksheet'])

    def get_user_data(self, telegram_id):
        records = self.users_worksheet.get_all_records()
        for record in records:
            if str(record['telegram_id']) == str(telegram_id):
                return record
        return None

    def save_user_data(self, user_data):
        existing_user = self.get_user_data(user_data['telegram_id'])

        row = [
            user_data['telegram_id'],
            user_data['first_name'],
            user_data['last_name'],
            user_data['age'],
            user_data['email'],
            user_data['language'],
            user_data['registration_date']
        ]

        if existing_user:
            cell = self.users_worksheet.find(str(user_data['telegram_id']))
            self.users_worksheet.update(f"A{cell.row}:G{cell.row}", [row])
        else:
            self.users_worksheet.append_row(row)

    def update_user_language(self, telegram_id, language):
        user = self.get_user_data(telegram_id)
        if user:
            cell = self.users_worksheet.find(str(telegram_id))
            self.users_worksheet.update_cell(cell.row, 6, language)

    def save_question_answer(self, telegram_id, question, answer, timestamp):
        row = [telegram_id, question, answer, timestamp]
        self.questions_worksheet.append_row(row)

    def get_user_questions(self, telegram_id):
        records = self.questions_worksheet.get_all_records()
        return [
            {'question': record['question'], 'answer': record['answer']}
            for record in records
            if str(record['telegram_id']) == str(telegram_id)
        ]
