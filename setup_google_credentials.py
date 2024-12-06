import os

# To set up your Google credentials
def setup_google_credentials():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"
    print("Google Cloud credentials set up successfully.")
