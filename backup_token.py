import os
import shutil

def backup_token(token_path='token.pickle', backup_path='token.pickle.bak'):
    if os.path.exists(token_path):
        shutil.copy2(token_path, backup_path)
        print(f"Backed up {token_path} to {backup_path}.")
    else:
        print(f"{token_path} not found. No backup created.")

if __name__ == "__main__":
    backup_token()
