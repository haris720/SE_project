"""
Configuration file for the AI Freelancer Evaluation System
"""

# MongoDB Configuration
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "freelancer_ai_db"
FREELANCERS_COLLECTION = "freelancers"
PROJECTS_COLLECTION = "projects"

# Model Paths
TRUST_SCORE_MODEL_PATH = "services/models/trust_score_model.pkl"
COST_MODEL_PATH = "models/cost_estimation_model.pkl"
TIME_MODEL_PATH = "models/time_estimation_model.pkl"
TFIDF_VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"

# Model Parameters
TRUST_SCORE_THRESHOLD = (0, 100)
MAX_FEATURES_TFIDF = 500
RANDOM_STATE = 42

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_TITLE = "AI Freelancer Evaluation System"
API_VERSION = "1.0.0"
