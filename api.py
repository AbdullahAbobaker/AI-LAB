# get a new token: https://dashboard.cohere.ai/

import getpass
import os

if "COHERE_API_KEY" not in os.environ:
    os.environ["COHERE_API_KEY"] = getpass.getpass("Cohere API Key:")

key = getpass.getpass("Cohere API Key:")
print(key)