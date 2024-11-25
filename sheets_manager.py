import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional

class SheetsManager:
    def __init__(self, credentials_file: str = '/home/mithun/Documents/atted/cerds/sheetcred.json', 
                 sheet_name: str = 'Attendance_Records',
                 admin_email: str = 'babbiraproject@gmail.com'):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, self.scope)
        self.client = gspread.authorize(self.creds)
        self.sheet_name = sheet_name
        self.admin_email = admin_email
        self.spreadsheet = self.get_or_create_sheet()
        print(f"Spreadsheet URL: {self.spreadsheet.url}")

    def get_or_create_sheet(self):
        try:
            spreadsheet = self.client.open(self.sheet_name)
            print("Found existing spreadsheet")
            return spreadsheet
        except gspread.SpreadsheetNotFound:
            print("Creating new spreadsheet...")
            spreadsheet = self.client.create(self.sheet_name)
            sheet = spreadsheet.sheet1
            
            # Initialize with headers
            sheet.update('A1:B1', [['Name', datetime.now().strftime('%Y-%m-%d')]])
            return spreadsheet

    def record_attendance(self, name: str, phone: str, position: int) -> bool:
        try:
            sheet = self.spreadsheet.sheet1
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get all values
            all_values = sheet.get_all_values()
            
            # If sheet is empty, initialize it
            if not all_values:
                sheet.update('A1:B1', [['Name', today]])
                all_values = [['Name', today]]
            
            # Get headers (first row)
            headers = all_values[0]
            
            # If today's date is not in headers, add it
            if today not in headers:
                next_col = len(headers) + 1
                sheet.update_cell(1, next_col, today)
            
            # Get all names (first column, excluding header)
            names = [row[0] for row in all_values[1:] if row]
            
            # Find or add name
            if name not in names:
                next_row = len(all_values) + 1
                sheet.update_cell(next_row, 1, name)
            
            return True
            
        except Exception as e:
            print(f"Error recording attendance: {str(e)}")
            return False