import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv

load_dotenv()

security = HTTPBasic()

USERNAME = os.getenv("SHOP_USERNAME")
PASSWORD = os.getenv("SHOP_PASSWORD")

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = credentials.username == USERNAME
    correct_password = credentials.password == PASSWORD

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
