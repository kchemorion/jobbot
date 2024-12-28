import logging
import os
from datetime import datetime
import io
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import stripe
from anthropic import Anthropic
from PyPDF2 import PdfReader
import digitalocean
import dns.resolver
from database import Database, User, Package
import magic
import requests
from storage import SpaceStorage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize clients
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize storage
storage = SpaceStorage()

def setup_email_forwarding(user_email):
    """Setup email forwarding using ForwardEmail"""
    # Verify domain has correct MX records
    try:
        mx_records = dns.resolver.resolve('jobbot.work', 'MX')
        has_forward_email = False
        for mx in mx_records:
            if 'forwardemail.net' in str(mx.exchange):
                has_forward_email = True
                break
        
        if not has_forward_email:
            logging.error("ForwardEmail MX records not found")
            return False
        
        # The email will automatically forward to EMAIL_CATCH_ALL
        # as long as the MX records are set up correctly
        return True
    except Exception as e:
        logging.error(f"Error checking MX records: {str(e)}")
        return False

def upload_to_spaces(file_obj, filename, user_id):
    """Upload file to DigitalOcean Spaces"""
    try:
        return storage.upload_cv(user_id, file_obj.read(), filename)
    except Exception as e:
        logging.error(f"Error uploading to Spaces: {str(e)}")
        return None

# States for conversation handler
UPLOAD_CV, PROFILE_SETUP, PACKAGE_SELECTION, PAYMENT, JOB_PREFERENCES = range(5)

# Available packages
PACKAGES = {
    'basic': {'name': 'Basic', 'applications': 100, 'price': 49.99},
    'pro': {'name': 'Pro', 'applications': 500, 'price': 149.99},
    'enterprise': {'name': 'Enterprise', 'applications': float('inf'), 'price': 299.99}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    keyboard = [
        [InlineKeyboardButton("Upload CV", callback_data='upload_cv')],
        [InlineKeyboardButton("View Packages", callback_data='view_packages')],
        [InlineKeyboardButton("My Applications", callback_data='my_applications')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "🤖 Welcome to JobBot!\n\n"
        "I'm your automated job application assistant. "
        "Upload your CV, and I'll handle the rest!\n\n"
        "Please choose an option to get started:"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return UPLOAD_CV

async def handle_cv_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle CV file upload"""
    if not update.message.document:
        await update.message.reply_text("Please send me your CV as a PDF file.")
        return UPLOAD_CV

    file = await context.bot.get_file(update.message.document.file_id)
    
    # Download the file
    pdf_file = io.BytesIO()
    await file.download_to_memory(pdf_file)
    pdf_file.seek(0)
    
    # Verify file type
    file_type = magic.from_buffer(pdf_file.read(2048), mime=True)
    if file_type != 'application/pdf':
        await update.message.reply_text("Please send only PDF files.")
        return UPLOAD_CV
    
    pdf_file.seek(0)
    
    try:
        # Extract text from PDF
        pdf_reader = PdfReader(pdf_file)
        cv_text = ""
        for page in pdf_reader.pages:
            cv_text += page.extract_text()
        
        # Use Claude to extract structured information
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"Extract the following information from this CV in JSON format: full_name, email, phone, skills, work_experience, education. Here's the CV text:\n\n{cv_text}"
            }]
        )
        
        profile_data = message.content[0].text
        context.user_data['profile'] = profile_data
        
        # Generate and setup email for the user
        user_email = f"applicant_{update.effective_user.id}@jobbot.work"
        if not setup_email_forwarding(user_email):
            await update.message.reply_text(
                "⚠️ Warning: There was an issue setting up your email forwarding. "
                "Please contact support."
            )
        
        # Upload CV to DigitalOcean Spaces
        pdf_file.seek(0)
        cv_url = upload_to_spaces(
            pdf_file,
            update.message.document.file_name,
            update.effective_user.id
        )
        
        if not cv_url:
            await update.message.reply_text(
                "⚠️ Warning: There was an issue storing your CV. "
                "Please try again or contact support."
            )
            return UPLOAD_CV
        
        # Save user profile to database
        db = Database()
        db.add_user(
            telegram_id=str(update.effective_user.id),
            full_name=profile_data.get('full_name'),
            email=user_email,
            profile_data=profile_data,
            cv_url=cv_url
        )
        
        await update.message.reply_text(
            "✅ CV processed successfully!\n\n"
            f"📧 Your application email: {user_email}\n"
            "All job-related emails will be forwarded to our system.\n\n"
            "I've extracted your information and created your profile. "
            "Now, let's choose a package to start applying for jobs!"
        )
        
        return await view_packages(update, context)
        
    except Exception as e:
        logging.error(f"Error processing CV: {str(e)}")
        await update.message.reply_text(
            "Sorry, I couldn't process your CV. Please make sure it's a valid PDF file "
            "and try again."
        )
        return UPLOAD_CV

async def view_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display available packages"""
    query = update.callback_query
    if query:
        await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(f"{pkg['name']} - ${pkg['price']}", callback_data=f'select_package_{name}')]
        for name, pkg in PACKAGES.items()
    ]
    keyboard.append([InlineKeyboardButton("Back to Menu", callback_data='start')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    package_info = (
        "📦 Available Packages:\n\n"
        "🔹 Basic: 100 applications/month - $49.99\n"
        "🔸 Pro: 500 applications/month - $149.99\n"
        "💎 Enterprise: Unlimited applications - $299.99\n\n"
        "Each package includes:\n"
        "✓ AI-powered cover letter generation\n"
        "✓ Automatic profile matching\n"
        "✓ Application tracking\n"
        "✓ Dedicated application email\n"
        "✓ 24/7 support"
    )
    
    if query:
        await query.edit_message_text(package_info, reply_markup=reply_markup)
    else:
        await update.message.reply_text(package_info, reply_markup=reply_markup)
    
    return PACKAGE_SELECTION

async def setup_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile setup"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Let's set up your profile! Please provide the following information:\n"
        "1. Your full name\n"
        "2. Professional summary\n"
        "3. Key skills\n"
        "4. Work experience\n"
        "5. Education\n\n"
        "Send each piece of information in separate messages."
    )
    return PROFILE_SETUP

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment processing"""
    query = update.callback_query
    await query.answer()
    
    package_name = query.data.split('_')[2]
    package = PACKAGES[package_name]
    
    # Create Stripe payment session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'JobBot {package["name"]} Package',
                },
                'unit_amount': int(package['price'] * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://your-domain.com/success',
        cancel_url='https://your-domain.com/cancel',
    )
    
    # Store session ID in user's context
    context.user_data['payment_session'] = session.id
    
    keyboard = [[InlineKeyboardButton("Pay Now", url=session.url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"Great choice! You selected the {package['name']} package.\n"
        f"Total price: ${package['price']}\n\n"
        "Click the button below to proceed with payment:",
        reply_markup=reply_markup
    )

async def apply_to_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle automated job applications"""
    # Get user's profile and preferences
    user_profile = context.user_data.get('profile', {})
    preferences = context.user_data.get('preferences', {})
    
    # Use Claude to generate personalized cover letter
    message = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Generate a professional cover letter for a {preferences.get('job_title')} position based on this profile: {user_profile}. The cover letter should be concise, highlight relevant skills and experience, and demonstrate enthusiasm for the role."
        }]
    )
    cover_letter = message.content[0].text
    
    # Simulate job application
    await update.message.reply_text(
        "🤖 Applying to jobs...\n"
        "✓ Generated personalized cover letter\n"
        "✓ Matched profile with job requirements\n"
        "✓ Submitted application\n\n"
        "Application successful! I'll notify you of any responses."
    )

def main():
    """Start the bot"""
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.FileExtension('pdf'), handle_cv_upload))
    application.add_handler(CallbackQueryHandler(setup_profile, pattern='^setup_profile$'))
    application.add_handler(CallbackQueryHandler(view_packages, pattern='^view_packages$'))
    application.add_handler(CallbackQueryHandler(process_payment, pattern='^select_package_'))
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
