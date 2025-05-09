
#ONLY USED TO CREATE TOKEN.PICKLE


from google_auth_oauthlib.flow import Flow
import pickle 

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_PATH = 'client_secrets.json'
TOKEN_PATH = 'token.pickle'

def authenticate():
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri='http://localhost:8080'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent')
    print(f"Please go to this URL and authorize the application: {auth_url}")
    
    # Get the authorization code from user input
    code = input("Enter the authorization code: ")
    
    # Exchange the authorization code for credentials
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Save the credentials
    with open(TOKEN_PATH, 'wb') as token:
        pickle.dump(credentials, token)
    
    print("Authentication successful! Token saved.")

if __name__ == '__main__':
    authenticate()