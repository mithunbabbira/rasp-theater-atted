import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional

class SheetsManager:
    def __init__(self, credentials_file: str = '/home/mithun/Documents/atted/cerds/sheetcred.json', 
                 sheet_name: str = 'Attendance_Records',
                 admin_email: str = 'babbiraproject@gmail.com'):
        try:
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
            
        except Exception as e:
            print(f"Initialization error: {str(e)}")
            raise

    def get_or_create_sheet(self):
        try:
            # Try to open existing sheet
            spreadsheet = self.client.open(self.sheet_name)
            print("Found existing spreadsheet")
            
            # Ensure admin has access to existing spreadsheet
            self.ensure_admin_access(spreadsheet)
            return spreadsheet
            
        except gspread.SpreadsheetNotFound:
            print("Creating new spreadsheet...")
            try:
                # Create new spreadsheet
                spreadsheet = self.client.create(self.sheet_name)
                
                # Share with admin email
                self.ensure_admin_access(spreadsheet)
                
                # Get the first sheet and update headers
                sheet = spreadsheet.sheet1
                headers = ['Date', 'Time', 'Name', 'Phone', 'Position']
                sheet.append_row(headers)
                print("Added headers to spreadsheet")
                
                return spreadsheet
                
            except Exception as e:
                print(f"Error creating spreadsheet: {str(e)}")
                raise

    def ensure_admin_access(self, spreadsheet):
        """Ensure admin has editor access to the spreadsheet"""
        try:
            # Share with editor permissions
            spreadsheet.share(
                self.admin_email,
                perm_type='user',
                role='writer',
                notify=True,
                email_message='Attendance sheet has been shared with you'
            )
            print(f"Granted editor access to {self.admin_email}")
        except Exception as e:
            print(f"Error setting permissions: {str(e)}")
            raise

    def find_today_attendance(self, sheet, name: str) -> Optional[int]:
        """
        Find if user already marked attendance today
        Returns row number if found, None otherwise
        """
        try:
            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get all records
            records = sheet.get_all_records()
            
            # Check each row
            for index, record in enumerate(records, start=2):  # start=2 because row 1 is header
                if record['Date'] == today and record['Name'] == name:
                    return index
            
            return None
            
        except Exception as e:
            print(f"Error finding today's attendance: {str(e)}")
            return None

    def record_attendance(self, name: str, phone: str, position: int) -> bool:
        """
        Record attendance in Google Sheets
        Updates existing record if user already marked attendance today
        """
        try:
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            time = now.strftime('%H:%M:%S')
            
            # Prepare row data
            row_data = [date, time, name, phone, position]
            
            # Get the first sheet
            sheet = self.spreadsheet.sheet1
            
            # Check if user already marked attendance today
            existing_row = self.find_today_attendance(sheet, name)
            
            if existing_row:
                # Update existing record
                for col, value in enumerate(row_data, start=1):
                    sheet.update_cell(existing_row, col, value)
                print(f"Updated attendance for {name} at {date} {time}")
            else:
                # Add new record
                sheet.append_row(row_data)
                print(f"Recorded new attendance for {name} at {date} {time}")
            
            return True
            
        except Exception as e:
            print(f"Error recording attendance: {str(e)}")
            return False

# Test code
if __name__ == "__main__":
    # Test multiple attendance marks on same day
    sheets = SheetsManager()
    
    # First attendance
    print("\nFirst attendance mark:")
    test_result = sheets.record_attendance("Test User", "1234567890", 1)
    print(f"Test record result: {test_result}")
    
    # Second attendance (should update)
    print("\nSecond attendance mark (same day):")
    test_result = sheets.record_attendance("Test User", "1234567890", 1)
    print(f"Test record result: {test_result}")