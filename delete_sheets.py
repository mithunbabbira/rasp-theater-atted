import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def delete_all_sheets():
    # Setup credentials
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds_path = '/home/mithun/Documents/atted/cerds/sheetcred.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    
    try:
        # List all spreadsheets
        spreadsheets = client.openall()
        
        if not spreadsheets:
            print("No spreadsheets found!")
            return
            
        print(f"Found {len(spreadsheets)} spreadsheets:")
        for i, spreadsheet in enumerate(spreadsheets, 1):
            print(f"{i}. {spreadsheet.title}")
        
        # Confirm before deletion
        confirm = input("\nAre you sure you want to delete all these spreadsheets? (yes/no): ")
        
        if confirm.lower() == 'yes':
            for spreadsheet in spreadsheets:
                client.del_spreadsheet(spreadsheet.id)
                print(f"Deleted: {spreadsheet.title}")
            print("\nAll spreadsheets have been deleted!")
        else:
            print("Operation cancelled.")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    delete_all_sheets() 