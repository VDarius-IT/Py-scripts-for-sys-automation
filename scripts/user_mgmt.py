import os
import subprocess
from utils.common_utils import log_event

def create_user(username, password):
    """Create a new system user with logging and error handling"""
    try:
        # Check if user already exists
        if _user_exists(username):
            log_event(f"User {username} already exists", "ERROR")
            return False
            
        # Execute Windows user creation command
        result = subprocess.run(
            ['net', 'user', username, password, '/add'],
            check=True,
            capture_output=True,
            text=True
        )
        log_event(f"User {username} created successfully")
        return True
    except subprocess.CalledProcessError as e:
        error_message = _get_user_error_message(e, "create")
        log_event(f"User creation failed: {error_message}", "ERROR")
        return False

def delete_user(username):
    """Delete a system user with logging and error handling"""
    try:
        # Check if user exists
        if not _user_exists(username):
            log_event(f"User {username} does not exist", "ERROR")
            return False
            
        # Execute Windows user deletion command
        subprocess.run(
            ['net', 'user', username, '/delete'],
            check=True,
            capture_output=True,
            text=True
        )
        log_event(f"User {username} deleted successfully")
        return True
    except subprocess.CalledProcessError as e:
        error_message = _get_user_error_message(e, "delete")
        log_event(f"User deletion failed: {error_message}", "ERROR")
        return False

def list_users():
    """List all system users with structured output"""
    try:
        # Get list of users
        result = subprocess.run(
            ['net', 'user'],
            check=True,
            capture_output=True,
            text=True
        )
        log_event("User list retrieved successfully")
        
        # Parse output to extract usernames
        return _parse_user_list(result.stdout)
        
    except subprocess.CalledProcessError as e:
        error_message = _get_user_error_message(e, "list")
        log_event(f"Failed to retrieve user list: {error_message}", "ERROR")
        return None

def _user_exists(username):
    """Check if a user exists on the system"""
    try:
        subprocess.run(
            ['net', 'user', username],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def _parse_user_list(raw_output):
    """Parse raw 'net user' output to extract usernames"""
    lines = raw_output.splitlines()
    users = []
    parsing = False
    
    for line in lines:
        line = line.strip()
        if line.startswith('-'):
            parsing = not parsing
            continue
        if parsing and line:
            users.extend(line.split())
            
    return users

def _get_user_error_message(error, operation):
    """Get descriptive error message based on error code"""
    error_codes = {
        0: "Success",
        1: "Incorrect function was called",
        2: "The system cannot find the file specified",
        21: "The device is not ready",
        1379: "The user account already exists",
        1381: "The password is too long",
        1382: "The password does not meet complexity requirements",
        2221: "The user name could not be found",
        2223: "The user name is invalid",
        2224: "The user account already exists",
        2225: "The user is not allowed to log on at this computer",
        2226: "The user is not allowed to log on during the specified times",
        2227: "The password is too short",
        2228: "The password has expired",
        2242: "The password is invalid"
    }
    
    base_message = error.stderr.strip() if error.stderr else "Unknown error"
    specific_message = error_codes.get(error.returncode, f"Unknown error code {error.returncode}")
    
    return f"{base_message} (Code: {error.returncode}) - {specific_message}"

if __name__ == "__main__":
    # Example usage
    print("User Management Module")
    print("1. Create User")
    print("2. Delete User")
    print("3. List Users")
    
    choice = input("Select operation (1-3): ")
    
    if choice == "1":
        username = input("Enter username: ")
        password = input("Enter password: ")
        if create_user(username, password):
            print(f"User {username} created successfully")
        else:
            print(f"Failed to create user {username}")
    
    elif choice == "2":
        username = input("Enter username to delete: ")
        if delete_user(username):
            print(f"User {username} deleted successfully")
        else:
            print(f"Failed to delete user {username}")
    
    elif choice == "3":
        users = list_users()
        if users:
            print("System Users:")
            print(users)
        else:
            print("Failed to retrieve user list")
    
    else:
        print("Invalid choice")
