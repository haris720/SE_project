"""
AI Cost & Time Estimation Service
Predicts project cost range and delivery time using Gradient Boosting (XGBoost/LightGBM)
with TF-IDF for text processing
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import joblib
import os   
import sys
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_connection import get_db_connection
from config import *


class CostTimeEstimationService:
    """Service for predicting project cost and delivery time"""
    
    def __init__(self, 
                 cost_model_path: str = COST_MODEL_PATH,
                 time_model_path: str = TIME_MODEL_PATH,
                 vectorizer_path: str = TFIDF_VECTORIZER_PATH,
                 use_lightgbm: bool = True):
        """
        Initialize the estimation service
        
        Args:
            cost_model_path: Path to save/load cost model
            time_model_path: Path to save/load time model
            vectorizer_path: Path to save/load TF-IDF vectorizer
            use_lightgbm: Use LightGBM if True, XGBoost if False
        """
        self.cost_model_path = cost_model_path
        self.time_model_path = time_model_path
        self.vectorizer_path = vectorizer_path
        self.use_lightgbm = use_lightgbm
        
        self.cost_model = None
        self.time_model = None
        self.vectorizer = None
        
        # Complexity encoding with 15% incremental multipliers
        self.complexity_map = {
            'Simple': 1.0,           # Base
            'Moderate': 1.15,        # 15% more than Simple
            'Complex': 1.3225,       # 15% more than Moderate (1.15 * 1.15)
            'Very Complex': 1.520875 # 15% more than Complex (1.3225 * 1.15)
        }
    
    def load_data_from_db(self):
        """Load project data from MongoDB"""
        db = get_db_connection()
        projects = db.get_all_projects()
        
        if not projects:
            raise ValueError("No project data found in database")
        
        df = pd.DataFrame(projects)
        return df
    
    def validate_description(self, description: str) -> dict:
        """
        Validate if the project description is meaningful and contains technical content
        
        Args:
            description: Project description text
            
        Returns:
            Dictionary with 'valid' (bool) and 'message' (str)
        """
        # Check 1: Minimum length
        if not description or len(description.strip()) < 10:
            return {
                'valid': False,
                'message': 'Irrelevant description'
            }
        
        # Remove extra spaces and check actual content
        clean_desc = ' '.join(description.split())
        
        # Check 2: Minimum word count (at least 3 words)
        words = clean_desc.split()
        if len(words) < 3:
            return {
                'valid': False,
                'message': 'Irrelevant description'
            }
        
        # Check 3: Repeated characters (gibberish like "hehehehe" or "aaaaaaa" or "iiiiii")
        repeated_pattern = re.compile(r'(.)\1{4,}')  # Same character repeated 5+ times
        if repeated_pattern.search(description):
            return {
                'valid': False,
                'message': 'Irrelevant description'
            }
        
        # Check for gibberish patterns (random characters with no vowels or structure)
        # Count vowels vs consonants ratio
        vowels = len(re.findall(r'[aeiouAEIOU]', description))
        consonants = len(re.findall(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]', description))
        
        if consonants > 0:
            vowel_ratio = vowels / (vowels + consonants)
            # Normal English has ~38% vowels, allow 15%-60% range
            if vowel_ratio < 0.15:
                return {
                    'valid': False,
                    'message': 'Irrelevant description'
                }
        
        # Check for common technical/project keywords (at least one should exist)
        technical_keywords = [
            # Software Development
            'build', 'create', 'develop', 'design', 'implement', 'website', 'app', 'application',
            'system', 'platform', 'software', 'program', 'code', 'database', 'api', 'interface',
            'mobile', 'web', 'desktop', 'integrate', 'deploy', 'feature', 'functionality', 'need',
            'require', 'want', 'looking', 'project', 'page', 'site', 'tool', 'service', 'product',
            'dashboard', 'portal', 'ecommerce', 'blog', 'forum', 'authentication', 'payment',
            'user', 'admin', 'data', 'report', 'analysis', 'automation', 'script', 'bot',
            
            # AI & Machine Learning
            'game', 'animation', 'visualization', 'model', 'algorithm', 'machine', 'learning',
            'ai', 'ml', 'neural', 'network', 'deep', 'training', 'prediction', 'classification',
            'regression', 'clustering', 'nlp', 'computer', 'vision', 'tensorflow', 'pytorch',
            
            # Cloud & Infrastructure
            'cloud', 'aws', 'azure', 'google', 'server', 'hosting', 'deployment', 'devops',
            'docker', 'kubernetes', 'microservices', 'scalable', 'infrastructure', 'cicd',
            'pipeline', 'containerization', 'serverless', 'lambda', 'ec2', 's3', 'gcp',
            
            # Database & Backend
            'mysql', 'postgresql', 'mongodb', 'redis', 'sql', 'nosql', 'backend', 'frontend',
            'fullstack', 'rest', 'graphql', 'node', 'django', 'flask', 'spring', 'express',
            
            # Mobile & Frontend
            'react', 'angular', 'vue', 'flutter', 'ios', 'android', 'kotlin', 'swift',
            'javascript', 'typescript', 'html', 'css', 'responsive', 'ui', 'ux', 'bootstrap',
            
            # IT & Base Technologies
            'network', 'security', 'firewall', 'vpn', 'linux', 'windows', 'unix', 'bash',
            'powershell', 'active', 'directory', 'ldap', 'dns', 'dhcp', 'tcp', 'ip', 'http',
            'https', 'ssl', 'tls', 'encryption', 'backup', 'recovery', 'monitoring', 'logging',
            
            # Data Science & Analytics
            'analytics', 'statistics', 'statistical', 'datascience', 'bigdata', 'hadoop', 'spark',
            'tableau', 'powerbi', 'excel', 'visualization', 'chart', 'graph', 'insight', 'metric',
            'kpi', 'dashboard', 'reporting', 'etl', 'datawarehouse', 'pipeline', 'processing',
            
            # Mathematics & Scientific
            'math', 'mathematics', 'mathematical', 'equation', 'formula', 'calculation', 'calculator',
            'algebra', 'geometry', 'calculus', 'trigonometry', 'statistics', 'probability',
            'optimization', 'simulation', 'numerical', 'computation', 'scientific', 'research',
            
            # English & Literature
            'english', 'literature', 'text', 'content', 'writing', 'editor', 'document', 'article',
            'blog', 'post', 'translation', 'language', 'grammar', 'spelling', 'word', 'sentence',
            'paragraph', 'essay', 'book', 'publication', 'manuscript', 'proofreading', 'editing',
            
            # E-commerce & Business
            'ecommerce', 'shopping', 'cart', 'checkout', 'stripe', 'paypal', 'inventory',
            'order', 'product', 'catalog', 'merchant', 'customer', 'crm', 'erp', 'pos',
            
            # Education & Training
            'education', 'learning', 'course', 'tutorial', 'training', 'teaching', 'student',
            'quiz', 'exam', 'test', 'assignment', 'grade', 'lms', 'elearning', 'online',
            
            # Blockchain & Crypto
            'blockchain', 'crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'smart', 'contract',
            'nft', 'defi', 'web3', 'solidity', 'wallet', 'token', 'mining',
            
            # IoT & Embedded
            'iot', 'embedded', 'arduino', 'raspberry', 'sensor', 'hardware', 'firmware',
            'microcontroller', 'automation', 'smart', 'device', 'connected'
        ]
        
        description_lower = description.lower()
        has_technical_word = any(keyword in description_lower for keyword in technical_keywords)
        
        if not has_technical_word:
            return {
                'valid': False,
                'message': 'Irrelevant description'
            }
        
        # Check average word length (gibberish often has unusual word lengths)
        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length < 2 or avg_word_length > 15:
            return {
                'valid': False,
                'message': 'Irrelevant description'
            }
        
        # Check for individual gibberish words (long words with poor vowel distribution)
        for word in words:
            if len(word) > 12:  # Only check very long words (increased from 10 to 12)
                word_vowels = len(re.findall(r'[aeiouAEIOU]', word))
                word_consonants = len(re.findall(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]', word))
                if word_consonants > 0:
                    word_vowel_ratio = word_vowels / (word_vowels + word_consonants)
                    # Individual word has very poor structure - relaxed from 20%-70% to 15%-75%
                    if word_vowel_ratio < 0.15 or word_vowel_ratio > 0.75:
                        return {
                            'valid': False,
                            'message': 'Irrelevant description'
                        }
            
            # Check for uncommon letter patterns in long words (gibberish detector)
            if len(word) > 8:
                # Check if word has unusual consonant clusters (6+ consonants in a row)
                # Increased from 4 to 6 to allow technical terms like 'deployment', 'scripts'
                consonant_clusters = re.findall(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]{6,}', word)
                if consonant_clusters:
                    return {
                        'valid': False,
                        'message': 'Irrelevant description'
                    }
                
                # Check for multiple 'q' without 'u' following (unusual in English)
                q_count = word.lower().count('q')
                qu_count = word.lower().count('qu')
                if q_count > 0 and qu_count < q_count:
                    return {
                        'valid': False,
                        'message': 'Irrelevant description'
                    }
        
        return {
            'valid': True,
            'message': 'Description is valid'
        }
    
    def validate_skills(self, skills: list) -> dict:
        """
        Validate if the skills list contains real technical skills
        
        Args:
            skills: List of skill names
            
        Returns:
            Dictionary with 'valid' (bool) and 'message' (str)
        """
        if not skills or len(skills) == 0:
            return {
                'valid': False,
                'message': 'At least one skill is required'
            }
        
        # Valid technical skills database (200+ common skills)
        valid_skills = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c', 'c++', 'c#', 'csharp', 'ruby',
            'php', 'swift', 'kotlin', 'go', 'golang', 'rust', 'scala', 'r', 'matlab', 'perl',
            'dart', 'elixir', 'haskell', 'lua', 'objective-c', 'sql', 'bash', 'shell', 'powershell',
            
            # Web Development
            'html', 'css', 'react', 'angular', 'vue', 'vuejs', 'nextjs', 'nuxt', 'svelte',
            'jquery', 'bootstrap', 'tailwind', 'sass', 'less', 'webpack', 'vite', 'nodejs',
            'node', 'express', 'nestjs', 'django', 'flask', 'fastapi', 'spring', 'laravel',
            
            # Mobile Development
            'android', 'ios', 'flutter', 'react-native', 'reactnative', 'xamarin', 'ionic',
            'cordova', 'swiftui', 'jetpack', 'compose',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'mssql', 'sqlserver',
            'cassandra', 'dynamodb', 'firebase', 'firestore', 'couchdb', 'neo4j', 'elasticsearch',
            'mariadb', 'cockroachdb',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'google-cloud', 'docker', 'kubernetes', 'k8s', 'jenkins',
            'gitlab', 'github', 'terraform', 'ansible', 'chef', 'puppet', 'vagrant', 'circleci',
            'travis', 'nginx', 'apache', 'linux', 'ubuntu', 'centos', 'debian', 'redhat',
            
            # Data Science & AI
            'machine-learning', 'deep-learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
            'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'opencv', 'nlp', 'computer-vision',
            'data-science', 'data-analysis', 'statistics', 'big-data', 'hadoop', 'spark', 'kafka',
            
            # Game Development
            'unity', 'unreal', 'godot', 'blender', 'maya', '3d-modeling', 'game-design',
            'game-development', 'opengl', 'directx', 'webgl', 'threejs',
            
            # Design & UI/UX
            'figma', 'sketch', 'adobe-xd', 'photoshop', 'illustrator', 'indesign', 'after-effects',
            'premiere', 'ui-design', 'ux-design', 'graphic-design', 'web-design', 'logo-design',
            
            # Testing & QA
            'selenium', 'junit', 'pytest', 'jest', 'mocha', 'chai', 'cypress', 'testng',
            'cucumber', 'testing', 'automation', 'qa', 'quality-assurance',
            
            # Blockchain
            'blockchain', 'solidity', 'ethereum', 'bitcoin', 'web3', 'smart-contracts',
            'hyperledger', 'crypto', 'nft', 'defi',
            
            # Other Technologies
            'git', 'rest-api', 'restful', 'graphql', 'api', 'microservices', 'oauth', 'jwt',
            'websocket', 'grpc', 'soap', 'xml', 'json', 'yaml', 'regex', 'agile', 'scrum',
            'jira', 'confluence', 'slack', 'trello', 'excel', 'powerbi', 'tableau', 'seo',
            'digital-marketing', 'content-writing', 'copywriting', 'technical-writing',
            
            # Mathematics & Science
            'mathematics', 'algebra', 'calculus', 'statistics', 'probability', 'physics',
            'chemistry', 'biology', 'engineering', 'mechanical', 'electrical', 'civil',
            
            # Languages & Content
            'english', 'spanish', 'french', 'german', 'chinese', 'japanese', 'translation',
            'writing', 'content-creation', 'blogging', 'editing', 'proofreading'
        ]
        
        # Check each skill
        invalid_skills = []
        for skill in skills:
            skill_clean = skill.strip().lower()
            
            # Skip empty skills
            if not skill_clean:
                invalid_skills.append(skill)
                continue
            
            # Check if skill is too short
            if len(skill_clean) < 2:
                invalid_skills.append(skill)
                continue
            
            # Check for gibberish patterns
            # 1. Repeated characters (e3e3e3e3)
            repeated_pattern = re.compile(r'(.{1,3})\1{3,}')
            if repeated_pattern.match(skill_clean):
                invalid_skills.append(skill)
                continue
            
            # 2. All same character (oooo, eee)
            if len(set(skill_clean)) == 1:
                invalid_skills.append(skill)
                continue
            
            # 3. Check if skill matches valid skills FIRST (before vowel ratio check)
            # This ensures common skills like "css", "html" are accepted
            is_valid = False
            for valid_skill in valid_skills:
                if valid_skill == skill_clean or valid_skill in skill_clean or skill_clean in valid_skill:
                    is_valid = True
                    break
            
            # If already validated as a known skill, skip other checks
            if is_valid:
                continue
            
            # 4. Very poor vowel ratio check (only for unknown skills)
            # Skip this check for skills with special characters (like C++, C#, .NET)
            if not re.search(r'[+#.]', skill_clean):
                vowels = len(re.findall(r'[aeiou]', skill_clean))
                consonants = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', skill_clean))
                if consonants > 0:
                    vowel_ratio = vowels / (vowels + consonants)
                    if vowel_ratio < 0.10 or vowel_ratio > 0.80:
                        invalid_skills.append(skill)
                        continue
            
            # 5. If not in valid list and failed vowel check, check structure patterns
            # Allow skills with dashes/spaces (multi-word skills)
            if '-' in skill_clean or ' ' in skill_clean:
                is_valid = True
            # Allow skills starting with common prefixes
            elif any(skill_clean.startswith(prefix) for prefix in ['front', 'back', 'full', 'web', 'mobile', 'data', 'cloud']):
                is_valid = True
            # Allow reasonable length single words (3-20 chars) with decent vowel ratio
            elif 3 <= len(skill_clean) <= 20:
                vowels = len(re.findall(r'[aeiou]', skill_clean))
                consonants = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', skill_clean))
                if consonants > 0:
                    vowel_ratio = vowels / (vowels + consonants)
                    if vowel_ratio > 0.15:
                        is_valid = True
            
            if not is_valid:
                invalid_skills.append(skill)
        
        # If any invalid skills found, reject
        if invalid_skills:
            return {
                'valid': False,
                'message': f'Invalid skills detected: {", ".join(invalid_skills[:3])}. Please enter valid technical skills.'
            }
        
        return {
            'valid': True,
            'message': 'Skills are valid'
        }
    
    def preprocess_data(self, df: pd.DataFrame, fit_vectorizer: bool = True):
        """
        Preprocess and engineer features including TF-IDF
        Priority order: 1) Complexity, 2) Skills, 3) Description
        
        Args:
            df: DataFrame with project data
            fit_vectorizer: If True, fit new vectorizer; if False, use existing
        
        Returns:
            X_cost, X_time, y_cost, y_time
        """
        # Initialize or use existing vectorizer
        if fit_vectorizer:
            self.vectorizer = TfidfVectorizer(
                max_features=MAX_FEATURES_TFIDF,
                ngram_range=(1, 2),
                stop_words='english',
                min_df=2
            )
            tfidf_features = self.vectorizer.fit_transform(df['description'])
        else:
            if self.vectorizer is None:
                raise ValueError("Vectorizer not initialized. Set fit_vectorizer=True first.")
            tfidf_features = self.vectorizer.transform(df['description'])
        
        # Convert TF-IDF to DataFrame - Description analysis (20% importance)
        tfidf_df = pd.DataFrame(
            tfidf_features.toarray(),
            columns=[f'tfidf_{i}' for i in range(tfidf_features.shape[1])]
        )
        # Apply moderate weight to description features
        tfidf_df = tfidf_df * 1.0
        
        # DESCRIPTION COMPLEXITY FEATURES (NEW) - Analyze description detail level
        # These features capture project scope from the description content
        description_word_count = df['description'].apply(lambda x: len(str(x).split()))
        description_char_count = df['description'].apply(lambda x: len(str(x)))
        description_sentence_count = df['description'].apply(lambda x: str(x).count('.') + str(x).count('!') + str(x).count('?'))
        
        # Technical keyword density (indicates complexity)
        technical_keywords = [
            'api', 'database', 'authentication', 'integration', 'deployment', 'cloud',
            'backend', 'frontend', 'dashboard', 'admin', 'payment', 'security',
            'responsive', 'real-time', 'automation', 'algorithm', 'optimization',
            'microservices', 'scalable', 'testing', 'ci/cd', 'docker', 'kubernetes'
        ]
        technical_density = df['description'].apply(
            lambda x: sum(1 for kw in technical_keywords if kw in str(x).lower())
        )
        
        # Description complexity score (0-1000 scale for strong influence)
        # Longer, more detailed descriptions = more complex projects = HIGHER cost
        # Scale up the values to ensure significant impact on predictions
        description_complexity = (
            (description_word_count / 50) * 300 +   # Word count: 300 points max
            (technical_density) * 40 +               # Technical keywords: 40 points each
            (description_sentence_count / 5) * 200   # Sentence structure: 200 points max
        )  # No cap - allow higher scores for very detailed descriptions
        
        # Numerical features with priority weights
        # 1. Complexity dropdown - Base multiplier (30% importance)
        complexity_multiplier = df['complexity'].map(self.complexity_map)
        complexity_weighted = complexity_multiplier * 10.0
        
        # 2. Description Complexity - PRIMARY FACTOR (50% importance)
        # This should be the strongest predictor - more details = more cost
        description_weighted = description_complexity * 2.5  # Strong multiplier
        
        # 3. Skills count - Secondary factor (20% importance)
        skills_weighted = df['skills_count'] * 8.0
        
        numerical_features = pd.DataFrame({
            'complexity_multiplier': complexity_multiplier,
            'complexity_weighted': complexity_weighted,
            'description_word_count': description_word_count,
            'description_char_count': description_char_count,
            'description_sentence_count': description_sentence_count,
            'technical_density': technical_density,
            'description_complexity': description_complexity,
            'description_weighted': description_weighted,
            'skills_weighted': skills_weighted,
            'skills_count': df['skills_count']  # Keep original for reference
        })
        
        # Combine features - numerical features (complexity & skills) come first
        X = pd.concat([numerical_features.reset_index(drop=True), tfidf_df], axis=1)
        
        # Targets
        y_cost = df['actual_cost'].copy()
        y_time = df['delivery_days'].copy()
        
        return X, y_cost, y_time
    
    def train_cost_model(self, X_train, y_train):
        """Train model for cost prediction"""
        print("💰 Training cost prediction model...")
        
        if self.use_lightgbm:
            print("   Using LightGBM...")
            self.cost_model = lgb.LGBMRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=10,
                num_leaves=50,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=RANDOM_STATE,
                verbose=-1
            )
        else:
            print("   Using XGBoost...")
            self.cost_model = xgb.XGBRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=10,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=RANDOM_STATE,
                verbosity=0
            )
        
        self.cost_model.fit(X_train, y_train)
        print("✓ Cost model training completed")
        return self.cost_model
    
    def train_time_model(self, X_train, y_train):
        """Train model for time prediction"""
        print("⏱️ Training time prediction model...")
        
        if self.use_lightgbm:
            print("   Using LightGBM...")
            self.time_model = lgb.LGBMRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=10,
                num_leaves=50,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=RANDOM_STATE,
                verbose=-1
            )
        else:
            print("   Using XGBoost...")
            self.time_model = xgb.XGBRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=10,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=RANDOM_STATE,
                verbosity=0
            )
        
        self.time_model.fit(X_train, y_train)
        print("✓ Time model training completed")
        return self.time_model
    
    def evaluate_model(self, model, X_test, y_test, model_name: str):
        """Evaluate model performance"""
        predictions = model.predict(X_test)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, predictions)
        mse = mean_squared_error(y_test, predictions)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, predictions)
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        
        metrics = {
            'Model': model_name,
            'MAE': mae,
            'MSE': mse,
            'RMSE': rmse,
            'R2 Score': r2,
            'MAPE': mape
        }
        
        return metrics, predictions
    
    def save_models(self):
        """Save trained models and vectorizer to disk"""
        os.makedirs(os.path.dirname(self.cost_model_path), exist_ok=True)
        
        joblib.dump(self.cost_model, self.cost_model_path)
        print(f"✓ Cost model saved to {self.cost_model_path}")
        
        joblib.dump(self.time_model, self.time_model_path)
        print(f"✓ Time model saved to {self.time_model_path}")
        
        joblib.dump(self.vectorizer, self.vectorizer_path)
        print(f"✓ TF-IDF vectorizer saved to {self.vectorizer_path}")
    
    def load_models(self):
        """Load trained models and vectorizer from disk"""
        if os.path.exists(self.cost_model_path) and \
           os.path.exists(self.time_model_path) and \
           os.path.exists(self.vectorizer_path):
            
            self.cost_model = joblib.load(self.cost_model_path)
            self.time_model = joblib.load(self.time_model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
            
            print("✓ Models loaded successfully")
            return True
        else:
            print("⚠ Model files not found")
            return False
    
    def predict_cost_and_time(self, project_data: dict) -> dict:
        """
        Predict cost range and delivery time for a project
        Priority: 1) Complexity, 2) Skills, 3) Description
        
        Args:
            project_data: Dictionary with keys:
                - description: str (project description)
                - skills_required: list (list of skills)
                - complexity: str (Simple/Moderate/Complex/Very Complex)
        
        Returns:
            Dictionary with predicted min_cost, max_cost, and delivery_days
            OR error dictionary if validation fails
        """
        if self.cost_model is None or self.time_model is None or self.vectorizer is None:
            raise ValueError("Models not loaded. Call load_models() first.")
        
        # Extract features
        description = project_data.get('description', '')
        skills = project_data.get('skills_required', [])
        complexity = project_data.get('complexity', 'Moderate')
        
        # VALIDATE DESCRIPTION FIRST - reject gibberish/nonsense
        validation_result = self.validate_description(description)
        if not validation_result['valid']:
            return {
                'error': True,
                'message': validation_result['message'],
                'min_cost': 0,
                'max_cost': 0,
                'estimated_cost': 0,
                'delivery_days': 0
            }
        
        # VALIDATE SKILLS - reject invalid/gibberish skills
        skills_validation = self.validate_skills(skills)
        if not skills_validation['valid']:
            return {
                'error': True,
                'message': skills_validation['message'],
                'min_cost': 0,
                'max_cost': 0,
                'estimated_cost': 0,
                'delivery_days': 0
            }
        
        # TF-IDF features for description analysis (20% importance)
        tfidf_features = self.vectorizer.transform([description])
        tfidf_df = pd.DataFrame(
            tfidf_features.toarray(),
            columns=[f'tfidf_{i}' for i in range(tfidf_features.shape[1])]
        )
        # Apply moderate weight to description features
        tfidf_df = tfidf_df * 1.0
        
        # DESCRIPTION COMPLEXITY FEATURES - Analyze description detail level
        description_word_count = len(description.split())
        description_char_count = len(description)
        description_sentence_count = description.count('.') + description.count('!') + description.count('?')
        
        # Technical keyword density
        technical_keywords = [
            'api', 'database', 'authentication', 'integration', 'deployment', 'cloud',
            'backend', 'frontend', 'dashboard', 'admin', 'payment', 'security',
            'responsive', 'real-time', 'automation', 'algorithm', 'optimization',
            'microservices', 'scalable', 'testing', 'ci/cd', 'docker', 'kubernetes'
        ]
        technical_density = sum(1 for kw in technical_keywords if kw in description.lower())
        
        # Description complexity score (0-1000 scale)
        description_complexity = (
            (description_word_count / 50) * 300 +
            (technical_density) * 40 +
            (description_sentence_count / 5) * 200
        )
        
        # Numerical features with priority weights
        complexity_multiplier = self.complexity_map.get(complexity, 1.15)
        skills_count = len(skills)
        
        # 1. Complexity dropdown - Base multiplier (30%)
        complexity_weighted = complexity_multiplier * 10.0
        
        # 2. Description Complexity - PRIMARY FACTOR (50%)
        description_weighted = description_complexity * 2.5
        
        # 3. Skills count - Secondary factor (20%)
        skills_weighted = skills_count * 8.0
        
        numerical_features = pd.DataFrame({
            'complexity_multiplier': [complexity_multiplier],
            'complexity_weighted': [complexity_weighted],
            'description_word_count': [description_word_count],
            'description_char_count': [description_char_count],
            'description_sentence_count': [description_sentence_count],
            'technical_density': [technical_density],
            'description_complexity': [description_complexity],
            'description_weighted': [description_weighted],
            'skills_weighted': [skills_weighted],
            'skills_count': [skills_count]
        })
        
        # Combine features - numerical (complexity & skills) come first
        X = pd.concat([numerical_features.reset_index(drop=True), tfidf_df], axis=1)
        
        # Predictions
        base_cost = self.cost_model.predict(X)[0]
        base_time = self.time_model.predict(X)[0]
        
        # MANUAL DESCRIPTION-BASED ADJUSTMENT (fix for broken training data)
        # The training data has fixed costs, so we manually scale based on description
        
        # Calculate description impact multiplier (1.0 to 3.0x)
        word_count_multiplier = 1.0 + (description_word_count / 100) * 0.8  # +0.8x per 100 words
        technical_multiplier = 1.0 + (technical_density * 0.15)  # +15% per keyword
        sentence_multiplier = 1.0 + (description_sentence_count / 10) * 0.3  # +30% per 10 sentences
        
        # Combined description multiplier (cap between 1.0 and 3.5x)
        description_multiplier = min(3.5, max(1.0,
            word_count_multiplier * 0.5 +
            technical_multiplier * 0.3 +
            sentence_multiplier * 0.2
        ))
        
        # Apply description multiplier to base cost
        predicted_cost = base_cost * description_multiplier
        
        # Time also increases with description complexity (but less dramatically)
        time_multiplier = 1.0 + (description_multiplier - 1.0) * 0.4  # 40% of cost increase
        predicted_time = base_time * time_multiplier
        
        # Calculate cost range (±15% for short descriptions, ±25% for long ones)
        range_variation = 0.15 + (description_multiplier - 1.0) * 0.05  # Wider range for complex projects
        min_cost = int(predicted_cost * (1 - range_variation))
        max_cost = int(predicted_cost * (1 + range_variation))
        
        # Round delivery days
        delivery_days = max(1, int(round(predicted_time)))
        
        return {
            'min_cost': min_cost,
            'max_cost': max_cost,
            'estimated_cost': int(predicted_cost),
            'delivery_days': delivery_days
        }


def train_cost_time_models(use_lightgbm: bool = True):
    """Main function to train cost and time estimation models"""
    model_type = "LightGBM" if use_lightgbm else "XGBoost"
    
    print("=" * 60)
    print(f"AI COST & TIME ESTIMATION MODEL TRAINING ({model_type})")
    print("=" * 60)
    
    # Initialize service
    service = CostTimeEstimationService(use_lightgbm=use_lightgbm)
    
    # Load data
    print("\n📊 Loading data from MongoDB...")
    df = service.load_data_from_db()
    print(f"✓ Loaded {len(df)} project records")
    
    # Preprocess data
    print("\n🔧 Preprocessing data with TF-IDF vectorization...")
    X, y_cost, y_time = service.preprocess_data(df, fit_vectorizer=True)
    print(f"✓ Features shape: {X.shape}")
    print(f"✓ TF-IDF features: {MAX_FEATURES_TFIDF}")
    
    # Split data
    print("\n✂️ Splitting data into train and test sets...")
    X_train, X_test, y_cost_train, y_cost_test, y_time_train, y_time_test = train_test_split(
        X, y_cost, y_time, test_size=0.2, random_state=RANDOM_STATE
    )
    print(f"✓ Train set: {X_train.shape[0]} samples")
    print(f"✓ Test set: {X_test.shape[0]} samples")
    
    # Train cost model
    print(f"\n🤖 Training cost prediction model with {model_type}...")
    service.train_cost_model(X_train, y_cost_train)
    
    # Train time model
    print(f"\n🤖 Training time prediction model with {model_type}...")
    service.train_time_model(X_train, y_time_train)
    
    # Evaluate cost model
    print("\n📈 Evaluating cost prediction model...")
    cost_metrics, cost_predictions = service.evaluate_model(
        service.cost_model, X_test, y_cost_test, "Cost Prediction"
    )
    
    print("\n💰 Cost Model Performance:")
    print("-" * 60)
    for metric, value in cost_metrics.items():
        if metric == 'Model':
            continue
        if 'MAPE' in metric:
            print(f"   {metric}: {value:.2f}%")
        else:
            print(f"   {metric}: {value:.2f}")
    
    # Evaluate time model
    print("\n📈 Evaluating time prediction model...")
    time_metrics, time_predictions = service.evaluate_model(
        service.time_model, X_test, y_time_test, "Time Prediction"
    )
    
    print("\n⏱️ Time Model Performance:")
    print("-" * 60)
    for metric, value in time_metrics.items():
        if metric == 'Model':
            continue
        if 'MAPE' in metric:
            print(f"   {metric}: {value:.2f}%")
        else:
            print(f"   {metric}: {value:.2f}")
    
    # Save models
    print("\n💾 Saving models and vectorizer...")
    service.save_models()
    
    # Test prediction
    print("\n🧪 Testing prediction with sample data...")
    sample_data = {
        'description': 'Build a machine learning model for customer churn prediction with Python and scikit-learn',
        'skills_required': ['Python', 'Machine Learning', 'Scikit-learn', 'Data Science'],
        'complexity': 'Complex'
    }
    
    prediction = service.predict_cost_and_time(sample_data)
    print(f"   Sample Input:")
    print(f"      Description: {sample_data['description']}")
    print(f"      Skills: {', '.join(sample_data['skills_required'])}")
    print(f"      Complexity: {sample_data['complexity']}")
    print(f"   Prediction:")
    print(f"      Cost Range: ${prediction['min_cost']:,} - ${prediction['max_cost']:,}")
    print(f"      Delivery Time: {prediction['delivery_days']} days")
    
    print("\n" + "=" * 60)
    print("✅ COST & TIME ESTIMATION MODEL TRAINING COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    # Train with LightGBM (change to False for XGBoost)
    train_cost_time_models(use_lightgbm=True)
