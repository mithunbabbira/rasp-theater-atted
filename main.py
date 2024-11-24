import time
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pyfingerprint.pyfingerprint import PyFingerprint

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

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = """
Available commands:
/start - Show this message
/enroll - Enroll a new fingerprint
/search - Search for a fingerprint
/delete - Delete a fingerprint
/count - Show number of stored fingerprints
"""
    await update.message.reply_text(commands)

async def enroll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        if positionNumber >= 0:
            await update.message.reply_text(f'Template already exists at position #{positionNumber}')
            return

        await update.message.reply_text('Remove finger...')
        time.sleep(2)
        await update.message.reply_text('Place same finger again...')

        while f.readImage() == False:
            pass

        f.convertImage(0x02)

        if f.compareCharacteristics() == 0:
            await update.message.reply_text('Fingers do not match!')
            return

        f.createTemplate()
        positionNumber = f.storeTemplate()
        await update.message.reply_text(f'Finger enrolled successfully!\nNew template position #{positionNumber}')

    except Exception as e:
        await update.message.reply_text(f'Operation failed! Error: {str(e)}')

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
            await update.message.reply_text(f'Found template at position #{positionNumber}\nAccuracy score: {accuracyScore}')

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

def main():
    app = Application.builder().token("8056496155:AAHeKa-PoFjBCPxybCRTttICrBDQXkmo3SU").build()

    # Add command handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('enroll', enroll_command))
    app.add_handler(CommandHandler('search', search_command))
    app.add_handler(CommandHandler('delete', delete_command))
    app.add_handler(CommandHandler('count', count_command))

    print('Bot started...')
    app.run_polling(poll_interval=1)

if __name__ == '__main__':
    main()
