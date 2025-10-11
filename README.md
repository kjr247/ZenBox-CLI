
This script fetches your recent unread emails from Gmail and displays a ranked list of senders by the number of emails received, including unsubscribe links if available.

# Zenbox Email Analyzer

This script fetches your recent unread emails from Gmail and displays a ranked list of senders by the number of emails received, including unsubscribe links if available.

## Setup Instructions

1. **Install Python 3.7+**
   - Download and install from https://www.python.org/downloads/

2. **Install required Python packages**
   - Open a terminal in this directory and run:
     ```bash
     pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib rich
     ```

3. **Set up Google Cloud Project and OAuth Credentials**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a new project (or select an existing one)
   - Click "+ CREATE CREDENTIALS" and choose "OAuth client ID"
   - If prompted, configure the consent screen (fill in required fields)
   - For "Application type", select **Desktop app**
   - Name it (e.g., "Zenbox Email Analyzer")
   - Click "Create"
   - Click "Download JSON" on the credentials you just created
   - Save the file as `credentials.json` (or update the script to use your filename) in this directory
   - Enable the Gmail API for your project:
     - Go to "APIs & Services" > "Library"
     - Search for "Gmail API" and click "Enable"

4. **Run the script**
   - In your terminal, run:
     ```bash
         python zenbox.py
     ```
   - The first time, a browser window will open for you to log in and authorize access to your Gmail account.

## Command-Line Flags

You can control the script's behavior with these flags:

- `--max-emails N` : Maximum number of unread emails to fetch and parse for top senders (default: 1000)
- `--show-unsubscribe` : Display unsubscribe links for up to `--max-unsubscribe` unread emails (prints links only, does not show top senders table)
- `--max-unsubscribe N` : Maximum number of unread emails to check for unsubscribe links with `--show-unsubscribe` (default: 100)

**Examples:**

Show top senders from up to 500 unread emails:
```bash
python zenbox.py --max-emails 500
```

Show unsubscribe links for up to 200 unread emails:
```bash
python zenbox.py --show-unsubscribe --max-unsubscribe 200
```

## Notes

- No secrets are hardcoded; credentials are loaded from your OAuth file and stored in `token.pickle` (which should not be checked into version control).
- The script only processes unread emails by default.
- The output table includes the sender, email count, and the first unsubscribe link found for each sender (if available).
- You can change the number of top senders shown by editing the `TOP_N_SENDERS` constant in the script.

---
