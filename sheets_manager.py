import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional
from gspread.exceptions import WorksheetNotFound
import os
from dotenv import load_dotenv

load_dotenv()

def get_env_variable(var_name: str, default: Optional[str] = None) -> str:
    value = os.getenv(var_name, default)
    if value is None:
        raise ValueError(f"Environment variable '{var_name}' is not set. Please check your .env file.")
    return value

# Validate environment variables at module level
try:
    WORKSHEET_INDEX = int(get_env_variable('WORKSHEET_INDEX', '0'))
    SHEET_NAME = get_env_variable('SHEET_NAME', 'Attendance_Records')
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please make sure the following environment variables are set correctly:")
    print("- WORKSHEET_INDEX (must be a valid integer)")
    print("- SHEET_NAME")
    exit(1)

class SheetsManager:
    def __init__(self, credentials_file: str = '/home/mithun/Documents/atted/cerds/sheetcred.json', 
                 sheet_name: Optional[str] = None,
                 admin_email: str = 'babbiraproject@gmail.com',
                 worksheet_index: Optional[int] = None):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, self.scope)
        self.client = gspread.authorize(self.creds)
        
        # Use environment variables with fallbacks
        self.sheet_name = sheet_name or SHEET_NAME
        self.admin_email = admin_email
        self.worksheet_index = worksheet_index if worksheet_index is not None else WORKSHEET_INDEX
        
        self.spreadsheet = self.get_or_create_sheet()
        self.worksheet = self.get_or_create_worksheet()
        print(f"Using worksheet index: {self.worksheet_index}")
        print(f"Using sheet name: {self.sheet_name}")
        print(f"Spreadsheet URL: {self.spreadsheet.url}")

    def get_or_create_worksheet(self):
        """Get existing worksheet or create new one at specified index"""
        try:
            # Try to get worksheet at specified index
            worksheet = self.spreadsheet.get_worksheet(self.worksheet_index)
            
            if worksheet is None:
                print(f"Creating new worksheet at index {self.worksheet_index}")
                # Create new worksheet
                worksheet = self.spreadsheet.add_worksheet(
                    title=f"Attendance Sheet {self.worksheet_index}", 
                    rows=1000, 
                    cols=100
                )
                # Initialize the new worksheet
                today = datetime.now().strftime('%Y-%m-%d')
                worksheet.update('A1:B1', [['Name', today]])
                print(f"Created and initialized new worksheet at index {self.worksheet_index}")
            
            return worksheet
            
        except WorksheetNotFound:
            print(f"Worksheet at index {self.worksheet_index} not found, creating new one...")
            worksheet = self.spreadsheet.add_worksheet(
                title=f"Attendance Sheet {self.worksheet_index}", 
                rows=1000, 
                cols=100
            )
            # Initialize the new worksheet
            today = datetime.now().strftime('%Y-%m-%d')
            worksheet.update('A1:B1', [['Name', today]])
            print(f"Created and initialized new worksheet at index {self.worksheet_index}")
            return worksheet
            
        except Exception as e:
            print(f"Error managing worksheet: {str(e)}")
            raise

    def get_or_create_sheet(self):
        try:
            spreadsheet = self.client.open(self.sheet_name)
            print("Found existing spreadsheet")
            return spreadsheet
        except gspread.SpreadsheetNotFound:
            print("Creating new spreadsheet...")
            spreadsheet = self.client.create(self.sheet_name)
            
            # Share with admin email
            spreadsheet.share(
                self.admin_email,
                perm_type='user',
                role='writer',
                notify=True
            )
            
            # Make it accessible to anyone with the link
            spreadsheet.share(
                None,
                perm_type='anyone',
                role='writer',
                notify=False,
                with_link=True
            )
            
            return spreadsheet

    def record_attendance(self, name: str, phone: str, position: int) -> bool:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%I:%M%p').lower()
            
            # Get all values from the current worksheet
            all_values = self.worksheet.get_all_values()
            
            # If sheet is empty, initialize it
            if not all_values:
                self.worksheet.update('A1:B1', [['Name', today]])
                all_values = [['Name', today]]
            
            headers = all_values[0]
            
            # Find or add today's date column
            if today in headers:
                date_col = headers.index(today) + 1
            else:
                date_col = len(headers) + 1
                self.worksheet.update_cell(1, date_col, today)
            
            # Get all names (first column, excluding header)
            names = [row[0] for row in all_values[1:] if row]
            
            # Find or add name and get its row
            if name in names:
                name_row = names.index(name) + 2
            else:
                name_row = len(all_values) + 1
                self.worksheet.update_cell(name_row, 1, name)
            
            # Mark attendance
            attendance_value = f"present-{current_time}"
            self.worksheet.update_cell(name_row, date_col, attendance_value)
            
            return True
            
        except Exception as e:
            print(f"Error recording attendance: {str(e)}")
            return False