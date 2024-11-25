import time
from datetime import datetime
from pyfingerprint.pyfingerprint import PyFingerprint
from database import DatabaseManager
from telegram.ext import ContextTypes
from telegram import Bot
from sheets_manager import SheetsManager

class AttendanceManager:
    def __init__(self, bot: Bot, creds_path: str = '/home/mithun/Documents/atted/cerds/sheetcred.json'):
        self.db = DatabaseManager()
        self.f = self.init_fingerprint()
        self.bot = bot
        self.CHAT_ID = -4552090363  # Hardcoded chat ID
        self.sheets = SheetsManager(credentials_file=creds_path)  # Pass the correct path

    def init_fingerprint(self):
        try:
            f = PyFingerprint('/dev/ttyAMA0', 57600, 0xFFFFFFFF, 0x00000000)
            if not f.verifyPassword():
                raise ValueError('The given fingerprint sensor password is wrong!')
            return f
        except Exception as e:
            print('The fingerprint sensor could not be initialized!')
            print('Exception message: ' + str(e))
            return None

    async def mark_attendance(self, timeout_seconds=20) -> tuple[bool, str]:
        """
        Attempt to read fingerprint and mark attendance for 20 seconds
        Returns: (success_status, message)
        """
        if not self.f:
            await self.bot.send_message(chat_id=self.CHAT_ID, text="Fingerprint sensor not initialized")
            return False, "Fingerprint sensor not initialized"

        start_time = time.time()
        await self.bot.send_message(chat_id=self.CHAT_ID, text="Waiting for finger...")

        try:
            # Wait for finger or timeout
            while time.time() - start_time < timeout_seconds:
                if self.f.readImage():
                    # Convert and search
                    self.f.convertImage(0x01)
                    result = self.f.searchTemplate()
                    position_number = result[0]
                    accuracy_score = result[1]

                    if position_number == -1:
                        msg = "No matching fingerprint found"
                        await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
                        return False, msg

                    # Get user details from database
                    user = self.db.get_user(position_number)
                    if not user:
                        msg = f"Found fingerprint at position {position_number} but no user details found"
                        await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
                        return False, msg

                    name, phone = user
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Record to Google Sheets
                    sheets_success = self.sheets.record_attendance(
                        name=name,
                        phone=phone,
                        position=position_number
                    )
                    
                    msg = f"Attendance marked for {name} at {timestamp}"
                    if not sheets_success:
                        msg += "\n(Warning: Failed to record in Google Sheets)"
                    
                    await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
                    return True, msg

                time.sleep(0.1)  # Small delay to prevent CPU overuse

            msg = "Timeout: No finger detected"
            await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
            return False, msg

        except Exception as e:
            msg = f"Error: {str(e)}"
            await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
            return False, msg 