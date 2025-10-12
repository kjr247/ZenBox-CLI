# Gmail Top Senders Analyzer
# See README above for setup and usage instructions.

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import collections
from typing import List, Dict
from rich.console import Console
from rich.table import Table
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import argparse
import webbrowser
from datetime import datetime

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify'
]
CREDENTIALS_FILE = 'ZenboxDesktop.client_secret_339182038683-r3aqgdrhqt30uk8on0na17upm31p8upe.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.pickle'
MAX_EMAILS = 1000
TOP_N_SENDERS = 25

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                sys.exit(f"Missing {CREDENTIALS_FILE}. See README for setup.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def fetch_email_ids(service, max_emails: int) -> List[str]:
    """Fetch up to max_emails message IDs from the user's inbox."""
    email_ids = []
    next_page_token = None
    while len(email_ids) < max_emails:
        response = service.users().messages().list(
            userId='me',
            maxResults=min(500, max_emails - len(email_ids)),
            pageToken=next_page_token,
            q='is:unread'
        ).execute()
        ids = [msg['id'] for msg in response.get('messages', [])]
        email_ids.extend(ids)
        next_page_token = response.get('nextPageToken')
        if not next_page_token or not ids:
            break
    return email_ids

def parse_sender_from_message(service, msg_id: str) -> str:
    """Extract sender's email address from a message."""
    msg = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From']).execute()
    headers = msg.get('payload', {}).get('headers', [])
    for header in headers:
        if header['name'].lower() == 'from':
            return header['value']
    return 'Unknown'


def get_unsubscribe_link_from_message(service, msg_id: str) -> str:
    """Extract the List-Unsubscribe link from a message, if present."""
    msg = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['List-Unsubscribe']).execute()
    headers = msg.get('payload', {}).get('headers', [])
    for header in headers:
        if header['name'].lower() == 'list-unsubscribe':
            return header['value']
    return None

def get_first_unsubscribe_link_for_sender(service, sender_email: str, max_search: int = 100):
    """Find the first unsubscribe link for a sender from their unread emails."""
    query = f'is:unread from:"{sender_email}"'
    response = service.users().messages().list(userId='me', q=query, maxResults=max_search).execute()
    messages = response.get('messages', [])
    for msg in messages:
        link_header = get_unsubscribe_link_from_message(service, msg['id'])
        if link_header:
            links = [l.strip(' <>') for l in link_header.split(',')]
            for link in links:
                if link.startswith('http') or link.startswith('mailto:'):
                    return link
    return ''

def display_unsubscribe_links_for_unread(service, max_search: int = 100):
    """Display unsubscribe links for all unread emails in the terminal."""
    print(f"Searching for unsubscribe links in unread emails (up to {max_search})...")
    query = 'is:unread'
    response = service.users().messages().list(userId='me', q=query, maxResults=max_search).execute()
    messages = response.get('messages', [])
    found = False
    for msg in messages:
        link_header = get_unsubscribe_link_from_message(service, msg['id'])
        if link_header:
            # The header can contain multiple links separated by commas
            links = [l.strip(' <>') for l in link_header.split(',')]
            print(f"\nUnsubscribe links for message ID {msg['id']}:")
            for link in links:
                print(f"  {link}")
            found = True
    if not found:
        print("No unsubscribe links found in unread emails.")

def count_senders(service, email_ids: List[str]) -> Dict[str, int]:
    """Count emails per sender."""
    sender_counts = collections.Counter()
    sender_to_ids = {}
    total = len(email_ids)
    for idx, msg_id in enumerate(email_ids, 1):
        try:
            msg = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From']).execute()
            headers = msg.get('payload', {}).get('headers', [])
            sender = None
            for h in headers:
                if h['name'].lower() == 'from':
                    sender = h['value']
                    break
            if sender:
                sender_counts[sender] = sender_counts.get(sender, 0) + 1
                sender_to_ids[msg_id] = sender
        except Exception as e:
            print(f"Error fetching message {msg_id}: {e}")
        if idx % 100 == 0 or idx == total:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processed {idx} emails...")
    return sender_counts, sender_to_ids


def display_top_senders_with_unsub(service, email_ids: list, sender_counts: Dict[str, int], top_n: int):
    """Display the top N senders in a table, including the first unsubscribe link from the already fetched unread emails."""
    sorted_senders = sender_counts.most_common(top_n)
    sender_unsub = {sender: '' for sender, _ in sorted_senders}
    # For each email, if sender is in top N, try to get the unsubscribe link
    for msg_id in email_ids:
        sender = parse_sender_from_message(service, msg_id)
        if sender in sender_unsub and not sender_unsub[sender]:
            link_header = get_unsubscribe_link_from_message(service, msg_id)
            if link_header:
                links = [l.strip(' <>') for l in link_header.split(',')]
                for link in links:
                    if link.startswith('http') or link.startswith('mailto:'):
                        sender_unsub[sender] = link
                        break
    def print_table():
        console = Console()
        table = Table(title=f"Top {top_n} Senders (Unread Emails)")
        table.add_column("Sender", style="cyan", no_wrap=True, width=100)
        table.add_column("Count", style="magenta", justify="right")
        table.add_column("Unsubscribe Link", style="green")
        for idx, (sender, count) in enumerate(sorted_senders, 1):
            unsub = sender_unsub[sender] if sender_unsub[sender] else "-"
            table.add_row(f"{idx}. {sender}", str(count), unsub)
        console.clear()
        console.print(table)

    while True:
        print_table()
        user_input = input(
            "\nOptions: [r]efresh table, [u] mark ALL as unread, [e] escape, or comma-separated numbers to mark as read, Enter to continue: "
        ).strip().lower()
        if user_input == 'r':
            continue
        elif user_input == 'u':
            all_senders = [sender for sender, _ in sorted_senders]
            print(f"Marking all emails from: {', '.join(all_senders)} as unread...")
            mark_senders_unread(service, all_senders)
            break
        elif user_input == 'e':
            print("Exiting...")
            break
        elif user_input == '':
            break
        else:
            # Only allow comma-separated numbers for marking as read
            try:
                indices = [int(x) for x in user_input.split(",") if x.strip().isdigit()]
                selected_senders = [sorted_senders[i-1][0] for i in indices if 1 <= i <= len(sorted_senders)]
                if selected_senders:
                    import time
                    for sender in selected_senders:
                        unsub_link = sender_unsub.get(sender)
                        if unsub_link and unsub_link != "-":
                            print(f"Opening unsubscribe link for {sender}: {unsub_link}")
                            try:
                                webbrowser.open(unsub_link)
                                time.sleep(1)  # Add a 1-second delay between openings
                            except Exception as e:
                                print(f"Failed to open unsubscribe link for {sender}: {e}")
                    print(f"Marking all emails from: {', '.join(selected_senders)} as read...")
                    mark_senders_read(service, selected_senders)
                    # Remove marked senders from sorted_senders and sender_unsub
                    sorted_senders = [(s, c) for (s, c) in sorted_senders if s not in selected_senders]
                    for s in selected_senders:
                        sender_unsub.pop(s, None)
                    if not sorted_senders:
                        print("No more senders to display.")
                        break
                else:
                    print("No valid senders selected.")
            except Exception as e:
                print(f"Error in selection: {e}")
            # Loop continues, reprinting updated table


def mark_senders_unread(service, senders: list):
    """Mark all emails from the given senders as unread (add 'UNREAD' label)."""
    import time
    for sender in senders:
        print(f"Finding emails from: {sender}")
        start = time.time()
        query = f"from:{sender}"
        email_ids = []
        next_page_token = None
        while True:
            response = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=500,
                pageToken=next_page_token
            ).execute()
            ids = [msg['id'] for msg in response.get('messages', [])]
            email_ids.extend(ids)
            next_page_token = response.get('nextPageToken')
            if not next_page_token or not ids:
                break
        print(f"  Found {len(email_ids)} emails. Marking as unread...")
        if email_ids:
            batch_size = 100
            for i in range(0, len(email_ids), batch_size):
                batch = email_ids[i:i+batch_size]
                service.users().messages().batchModify(
                    userId='me',
                    body={
                        'ids': batch,
                        'addLabelIds': ['UNREAD'],
                        'removeLabelIds': []
                    }
                ).execute()
                print(f"    Marked {i+len(batch)} of {len(email_ids)} as unread.")
                time.sleep(0.5)
        end = time.time()
        print(f"Done marking {sender} emails as unread. Took {end - start:.2f} seconds.\n")

def mark_senders_read(service, senders: list):
    """Mark all emails from the given senders as read (remove 'UNREAD' label)."""
    import time
    for sender in senders:
        print(f"Finding emails from: {sender}")
        start = time.time()
        query = f"from:{sender}"
        email_ids = []
        next_page_token = None
        while True:
            response = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=500,
                pageToken=next_page_token
            ).execute()
            ids = [msg['id'] for msg in response.get('messages', [])]
            email_ids.extend(ids)
            next_page_token = response.get('nextPageToken')
            if not next_page_token or not ids:
                break
        print(f"  Found {len(email_ids)} emails. Marking as read...")
        if email_ids:
            batch_size = 100
            for i in range(0, len(email_ids), batch_size):
                batch = email_ids[i:i+batch_size]
                service.users().messages().batchModify(
                    userId='me',
                    body={
                        'ids': batch,
                        'addLabelIds': [],
                        'removeLabelIds': ['UNREAD']
                    }
                ).execute()
                print(f"    Marked {i+len(batch)} of {len(email_ids)} as read.")
                time.sleep(0.5)
        end = time.time()
        print(f"Done marking {sender} emails as read. Took {end - start:.2f} seconds.\n")

def main():
    """Main execution flow."""
    parser = argparse.ArgumentParser(description="Gmail Top Senders Analyzer")
    parser.add_argument('--show-unsubscribe', action='store_true', help='Display unsubscribe links for unread emails')
    parser.add_argument('--max-unsubscribe', type=int, default=100, help='Max unread emails to check for unsubscribe links')
    parser.add_argument('--max-emails', type=int, default=MAX_EMAILS, help='Max unread emails to fetch and parse for top senders')
    args = parser.parse_args()

    service = authenticate_gmail()

    if args.show_unsubscribe:
        display_unsubscribe_links_for_unread(service, args.max_unsubscribe)
        return

    print("Fetching email IDs...")
    email_ids = fetch_email_ids(service, args.max_emails)
    if not email_ids:
        sys.exit("No emails found.")
    print(f"Fetched {len(email_ids)} emails. Parsing senders...")
    import time
    start_parse = time.time()
    sender_counts, sender_to_ids = count_senders(service, email_ids)
    end_parse = time.time()
    print(f"Sender parsing took {end_parse - start_parse:.2f} seconds.")
    if not sender_counts:
        sys.exit("No senders found.")
    print(f"\nTop {TOP_N_SENDERS} senders:\n")
    display_top_senders_with_unsub(service, email_ids, sender_counts, TOP_N_SENDERS)

if __name__ == '__main__':
    main()
