import os
from google_auth_oauthlib.flow import InstalledAppFlow

# The permissions your API needs
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/tasks.readonly',
    'https://www.googleapis.com/auth/youtube.readonly'
]

def authenticate_account(account_name):
    token_filename = f"token_{account_name}.json"
    
    # This looks for the credentials.json file you downloaded from Google Cloud
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    
    # prompt='consent' forces the account selector to appear so you can switch accounts
    creds = flow.run_local_server(port=0, prompt='consent')
    
    # Save the VIP pass for this specific account
    with open(token_filename, 'w') as token_file:
        token_file.write(creds.to_json())
    print(f"\nSuccess! Saved credentials to {token_filename}")



if __name__ == '__main__':
    name = input("Enter a name for this account (e.g., 'primary', 'second_channel'): ")
    authenticate_account(name)