import os
from firebase_admin import credentials, initialize_app

cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "firebase.json"))
initialize_app(cred)
