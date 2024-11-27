import time
from datetime import datetime
from pyfingerprint.pyfingerprint import PyFingerprint
from database import DatabaseManager
from telegram.ext import ContextTypes
from telegram import Bot
from sheets_manager import SheetsManager
import os
from dotenv import load_dotenv

load_dotenv()

class AttendanceManager:
    def __init__(self, bot: Bot, creds_path: str = '/home/mithun/Documents/atted/cerds/sheetcred.json'):
        self.db = DatabaseManager()
        self.f = self.init_fingerprint()
        self.bot = bot
        self.CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))
        
        # Get worksheet index from env
        worksheet_index = int(os.getenv('WORKSHEET_INDEX', '0'))  # Default to 0 if not set
        
        self.sheets = SheetsManager(
            credentials_file=creds_path,
            worksheet_index=worksheet_index
        )

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
                    
                    # Update last present date in database
                    self.db.update_last_present_date(position_number)
                    
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

    async def verify_attendance(self, user_position: int) -> tuple[bool, str]:
        """
        Verify if the scanned fingerprint matches the given user position
        Returns: (success_status, message)
        """
        if not self.f:
            await self.bot.send_message(chat_id=self.CHAT_ID, text="Fingerprint sensor not initialized")
            return False, "Fingerprint sensor not initialized"

        start_time = time.time()
        await self.bot.send_message(chat_id=self.CHAT_ID, text="Waiting for finger...")

        try:
            # Wait for finger or timeout
            while time.time() - start_time < 20:  # 20 seconds timeout
                if self.f.readImage():
                    # Convert and search
                    self.f.convertImage(0x01)
                    result = self.f.searchTemplate()
                    position_number = result[0]

                    if position_number == -1:
                        msg = "No matching fingerprint found"
                        await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
                        return False, msg

                    # Compare with expected position
                    if position_number == user_position:
                        # Get user name from database
                        user = self.db.get_user(position_number)
                        if user:
                            name, _ = user
                            msg = f"Attendance marked for {name}"
                            await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
                            return True, msg
                    else:
                        msg = "Fingerprint does not match the expected user"
                        await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
                        return False, msg

                    time.sleep(0.1)

            msg = "Timeout: No finger detected"
            await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
            return False, msg

        except Exception as e:
            msg = f"Error: {str(e)}"
            await self.bot.send_message(chat_id=self.CHAT_ID, text=msg)
            return False, msg 