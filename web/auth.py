"""
Authentication module for user management
Handles signup, login, and user validation
"""

import bcrypt
from database.db_connection import DatabaseConnection
from typing import Optional, Dict
import re
from datetime import datetime


class AuthService:
    def __init__(self):
        self.db = DatabaseConnection()
        self.users_collection = self.db.get_collection("users")
        self.users_collection.create_index("email", unique=True)
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        if len(password) > 50:
            return False, "Password must be less than 50 characters"
        return True, "Password is valid"
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    
    def signup(self, email: str, password: str, user_type: str, name: str) -> Dict:
        """
        Create a new user account
        Returns: {'success': bool, 'message': str, 'user_id': str}
        """
        # Validate email format
        if not self.validate_email(email):
            return {
                'success': False,
                'message': 'Invalid email format',
                'user_id': None
            }
        
        # Validate password
        is_valid, msg = self.validate_password(password)
        if not is_valid:
            return {
                'success': False,
                'message': msg,
                'user_id': None
            }
        
        # Validate user type
        if user_type not in ['freelancer', 'client']:
            return {
                'success': False,
                'message': 'User type must be either freelancer or client',
                'user_id': None
            }
        
        # Check if email already exists
        existing_user = self.users_collection.find_one({'email': email.lower()})
        if existing_user:
            return {
                'success': False,
                'message': 'An account with this email already exists',
                'user_id': None
            }
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Create user document
        user_doc = {
            'email': email.lower(),
            'password': hashed_password,
            'name': name,
            'user_type': user_type,
            'created_at': datetime.utcnow()
        }
        
        # Insert into database
        try:
            result = self.users_collection.insert_one(user_doc)
            return {
                'success': True,
                'message': 'Account created successfully',
                'user_id': str(result.inserted_id)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Database error: {str(e)}',
                'user_id': None
            }
    
    def login(self, email: str, password: str) -> Dict:
        """
        Authenticate user and return user data
        Returns: {'success': bool, 'message': str, 'user': dict}
        """
        # Find user by email
        user = self.users_collection.find_one({'email': email.lower()})
        
        if not user:
            return {
                'success': False,
                'message': 'Invalid email or password',
                'user': None
            }
        
        # Verify password
        if not self.verify_password(password, user['password']):
            return {
                'success': False,
                'message': 'Invalid email or password',
                'user': None
            }
        
        # Return user data (without password)
        user_data = {
            'user_id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'user_type': user['user_type']
        }
        
        return {
            'success': True,
            'message': 'Login successful',
            'user': user_data
        }
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user data by ID"""
        from bson import ObjectId
        try:
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if user:
                return {
                    'user_id': str(user['_id']),
                    'email': user['email'],
                    'name': user['name'],
                    'user_type': user['user_type']
                }
        except:
            return None
        return None
