import os
from database.db_manager import DatabaseManager
from utils.security import encrypt_data, decrypt_data, verify_password

def run_tests():
    print("Running Tests...")
    
    # 1. Test AES-256 Encryption/Decryption
    secret = "my_super_secret_password"
    encrypted = encrypt_data(secret)
    decrypted = decrypt_data(encrypted)
    assert secret == decrypted, "Encryption/Decryption failed!"
    assert verify_password(secret, encrypted), "Password Verification failed!"
    print("AES-256 Encryption Tests Passed.")
    
    # 2. Test DB Initialization
    db = DatabaseManager()
    print("Database Initialized.")
    
    # Wait for DB create user since 'admin' is created by default
    admin_user = db.get_user_by_username('admin')
    assert admin_user is not None, "Admin user not created!"
    print("Admin access verified.")
    
    # 3. Test Create User
    username = "testuser"
    password = "password123"
    success = db.create_user(username, password, recovery_email="test@example.com")
    assert success, "Failed to create user!"
    print("User Creation Passed.")
    
    # 4. Test Authenticate User
    auth_user = db.authenticate_user("testuser", "password123")
    assert auth_user is not None, "Authentication Failed!"
    assert auth_user['username'] == "testuser", "Username mismatch!"
    print("User Authentication Passed.")
    
    # 5. Test Invalid login
    invalid_auth = db.authenticate_user("testuser", "wrongpassword")
    assert invalid_auth is None, "Authentication should have failed!"
    print("Invalid login check Passed.")
    
    # Cleanup DB
    os.remove(os.path.join(os.path.dirname(__file__), 'database', 'acadence.db'))
    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()
