# JobBot - Automated Job Application Bot

JobBot is a Telegram bot that automates the job application process. It handles CV uploads, manages email forwarding, and helps users apply to multiple jobs efficiently.

## Features

- CV Upload and Processing
- Dedicated Email Address for Each User
- Multiple Subscription Packages
- Secure File Storage with DigitalOcean Spaces
- Automated Job Applications
- Payment Processing with Stripe

## Prerequisites

- Docker and Docker Compose
- DigitalOcean Account (for Spaces)
- Telegram Bot Token
- Stripe Account
- Domain Name (for email forwarding)

## Environment Variables

Copy `.env.example` to `.env` and fill in the required variables:

```bash
# Telegram Configuration
TELEGRAM_TOKEN=your_telegram_bot_token

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key

# Stripe Configuration
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key

# DigitalOcean Configuration
DO_ACCESS_TOKEN=your_digitalocean_token
DO_SPACE_NAME=jobbot-storage
DO_REGION=fra1
DO_ENDPOINT=fra1.digitaloceanspaces.com

# Database Configuration
DATABASE_URL=postgresql://jobbot:jobbot_password@db:5432/jobbot_db

# Email Configuration
EMAIL_DOMAIN=jobbot.work
EMAIL_CATCH_ALL=your_catch_all_email@example.com
```

## Deployment

1. Set up DNS Records:
   ```
   # MX Records for ForwardEmail
   @ MX 10 mx1.forwardemail.net
   @ MX 20 mx2.forwardemail.net
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

3. Initialize the database:
   ```bash
   docker-compose exec bot python -c "from database import Database; Database().create_tables()"
   ```

## Subscription Packages

- Basic: 100 applications/month - $49.99
- Pro: 500 applications/month - $149.99
- Enterprise: Unlimited applications - $299.99

## Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   python bot.py
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
