import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def create_user(email: str, password: str):
    """
    Creates a new user with the given email and password.
    """
    response = supabase.auth.sign_up({"email": email, "password": password})
    return response

def sign_in_user(email: str, password: str):
    """
    Signs in a user with the given email and password.
    """
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    return response

def sign_out_user():
    """
    Signs out the currently authenticated user.
    """
    response = supabase.auth.sign_out()
    return response

def get_user():
    """
    Retrieves the currently authenticated user.
    """
    response = supabase.auth.get_user()
    return response.user

def delete_user(user_id: str):
    """
    Deletes a user by their ID.
    """
    response = supabase.auth.admin.delete_user(user_id)
    return response

def save_user_credentials(data: dict):
    """
    Saves user credentials to the database.
    """
    response = supabase.table("credentials").upsert(data).execute()
    return response

def get_user_credentials():
    """
    Retrieves user credentials from the database.
    """
    user_id = supabase.auth.get_user().user.id
    response = supabase.table("credentials").select("*").eq("user_id", user_id).execute()
    return response.data