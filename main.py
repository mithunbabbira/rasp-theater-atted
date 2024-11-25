import time
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from pyfingerprint.pyfingerprint import PyFingerprint
from database import DatabaseManager
from attendance import AttendanceManager
import asyncio
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

# Then you can access the variables like this:
CREDS_FILE = os.getenv('GOOGLE_SHEETS_CREDS_FILE')
SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME')

# Initialize fingerprint sensor
def init_fingerprint():
    try:
        f = PyFingerprint('/dev/ttyAMA0', 57600, 0xFFFFFFFF, 0x00000000)
        if not f.verifyPassword():
            raise ValueError('The given fingerprint sensor password is wrong!')
        return f
    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        return None

# Add these states after the imports
ENTER_NAME, ENTER_PHONE, SCAN_FINGER = range(3)

# Initialize database
db = DatabaseManager()

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = """
Available commands:
/start - Show this message
/enroll - Enroll a new fingerprint
/search - Search for a fingerprint
/delete - Delete a fingerprint
/count - Show number of stored fingerprints
/attendance - Mark attendance
"""
    await update.message.reply_text(commands)

async def enroll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your name:")
    return ENTER_NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Please enter your phone number:")
    return ENTER_PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    
    f = init_fingerprint()
    if not f:
        await update.message.reply_text("Failed to initialize sensor!")
        return ConversationHandler.END

    try:
        await update.message.reply_text('Place your finger on the sensor...')
        while f.readImage() == False:
            pass
        
        f.convertImage(0x01)
        result = f.searchTemplate()
        positionNumber = result[0]

        if positionNumber >= 0:
            await update.message.reply_text(f'Template already exists at position #{positionNumber}')
            return ConversationHandler.END

        await update.message.reply_text('Remove finger...')
        time.sleep(2)
        await update.message.reply_text('Place same finger again...')

        while f.readImage() == False:
            pass

        f.convertImage(0x02)

        if f.compareCharacteristics() == 0:
            await update.message.reply_text('Fingers do not match!')
            return ConversationHandler.END

        f.createTemplate()
        positionNumber = f.storeTemplate()
        
        # Store user details in database
        if db.add_user(positionNumber, context.user_data['name'], context.user_data['phone']):
            await update.message.reply_text(
                f'Finger enrolled successfully!\n'
                f'New template position #{positionNumber}\n'
                f'Name: {context.user_data["name"]}\n'
                f'Phone: {context.user_data["phone"]}'
            )
        else:
            await update.message.reply_text('Failed to store user details in database')

    except Exception as e:
        await update.message.reply_text(f'Operation failed! Error: {str(e)}')
    
    return ConversationHandler.END

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = init_fingerprint()
    if not f:
        await update.message.reply_text("Failed to initialize sensor!")
        return

    try:
        await update.message.reply_text('Place your finger on the sensor...')
        while f.readImage() == False:
            pass

        f.convertImage(0x01)
        result = f.searchTemplate()
        positionNumber = result[0]
        accuracyScore = result[1]

        if positionNumber == -1:
            await update.message.reply_text('No match found!')
        else:
            # Get user details from database
            user = db.get_user(positionNumber)
            if user:
                name, phone = user
                await update.message.reply_text(
                    f'Found template at position #{positionNumber}\n'
                    f'Accuracy score: {accuracyScore}\n'
                    f'Name: {name}\n'
                    f'Phone: {phone}'
                )
            else:
                await update.message.reply_text(
                    f'Found template at position #{positionNumber}\n'
                    f'Accuracy score: {accuracyScore}\n'
                    f'No user details found in database'
                )

    except Exception as e:
        await update.message.reply_text(f'Operation failed! Error: {str(e)}')

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Please provide position number: /delete <position>')
        return

    f = init_fingerprint()
    if not f:
        await update.message.reply_text("Failed to initialize sensor!")
        return

    try:
        position = int(context.args[0])
        if f.deleteTemplate(position):
            # Also delete from database
            db.delete_user(position)
            await update.message.reply_text(f'Template at position {position} deleted successfully!')
        else:
            await update.message.reply_text('Failed to delete template!')
    except Exception as e:
        await update.message.reply_text(f'Operation failed! Error: {str(e)}')

async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = init_fingerprint()
    if not f:
        await update.message.reply_text("Failed to initialize sensor!")
        return

    try:
        count = f.getTemplateCount()
        capacity = f.getStorageCapacity()
        await update.message.reply_text(f'Currently used templates: {count}/{capacity}')
    except Exception as e:
        await update.message.reply_text(f'Operation failed! Error: {str(e)}')

async def mark_attendance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    creds_path = '/home/mithun/Documents/atted/cerds/sheetcred.json'
    attendance_mgr = AttendanceManager(context.bot, creds_path=creds_path)
    success, message = await attendance_mgr.mark_attendance()
    # No need to reply to the original message since all updates are sent to the specific chat

def main():
    app = Application.builder().token("8056496155:AAHeKa-PoFjBCPxybCRTttICrBDQXkmo3SU").build()

    # Create conversation handler for enrollment
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('enroll', enroll_command)],
        states={
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        },
        fallbacks=[],
    )

    # Add command handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(conv_handler)  # Add the conversation handler
    app.add_handler(CommandHandler('search', search_command))
    app.add_handler(CommandHandler('delete', delete_command))
    app.add_handler(CommandHandler('count', count_command))
    app.add_handler(CommandHandler('attendance', mark_attendance_command))

    print('Bot started...')
    app.run_polling(poll_interval=1)

if __name__ == '__main__':
    main()
