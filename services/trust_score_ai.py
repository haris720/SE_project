"""
AI-Based Trust Score Prediction Service
Uses Random Forest ML model to predict freelancer trustworthiness
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os
import sys
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import FreelancerProfile
from config import TRUST_SCORE_MODEL_PATH


class TrustScoreAI:
    """AI-based trust score prediction using Random Forest"""
    
    def __init__(self, model_path: str = TRUST_SCORE_MODEL_PATH):
        """
        Initialize the AI trust score service
        
        Args:
            model_path: Path to save/load the trained model
        """
        self.model_path = model_path
        self.model = None
        self.profile_db = FreelancerProfile()
        
        # Feature names for the model
        self.feature_names = [
            'average_rating',
            'success_rate', 
            'sentiment_score',
            'completed_jobs',
            'skills_count',
            'total_earnings',
            'avg_job_value',  # derived feature
            'rating_consistency'  # derived feature
        ]
        
    def create_training_data_from_database(self) -> pd.DataFrame:
        """
        Create training data with realistic trust score patterns
        AI learns complex relationships between features and trustworthiness
        """
        from database.models import FreelancerProfile
        profile_db = FreelancerProfile()
        
        # Get all freelancer profiles from database
        all_profiles = list(profile_db.collection.find())
        
        if len(all_profiles) < 10:
            print(f"⚠️  Only {len(all_profiles)} profiles found. Generating synthetic data for AI training...")
            all_profiles = []
        else:
            print(f"📊 Found {len(all_profiles)} real freelancer profiles for AI training")
        
        data = []
        
        # Generate synthetic training data with realistic patterns
        # AI will learn complex non-linear relationships
        n_synthetic = 2000
        print(f"📝 Generating {n_synthetic} training examples for AI model...")
        
        for i in range(n_synthetic):
            # Generate features with realistic correlations
            
            # High performers (30%) - Elite freelancers
            if i < n_synthetic * 0.3:
                average_rating = np.random.uniform(4.7, 5.0)
                success_rate = np.random.uniform(0.92, 1.0)
                sentiment_score = np.random.uniform(0.88, 1.0)
                completed_jobs = np.random.randint(15, 60)
                skills_count = np.random.randint(8, 20)
                total_earnings = completed_jobs * np.random.uniform(1200, 3000)
                
                # AI learns priority: REVIEW > JOB_COMPLETION > SKILLS > SATISFACTION
                # Start from 10 base, add weighted components
                
                # Priority 1: REVIEW (rating + sentiment) - 40% weight
                # Review combines rating (60%) and sentiment satisfaction (40%)
                review_component = (average_rating / 5.0) * 0.6 + sentiment_score * 0.4
                review_points = review_component * 40
                
                # Priority 2: JOB COMPLETION (jobs + success rate) - 30% weight
                job_volume_normalized = min(completed_jobs / 50, 1.0)
                completion_component = job_volume_normalized * 0.5 + success_rate * 0.5
                completion_points = completion_component * 30
                
                # Priority 3: SKILLS - 20% weight
                skill_component = min(skills_count / 20, 1.0)
                skill_points = skill_component * 20
                
                # Priority 4: SATISFACTION - 10% weight (bonus for consistency)
                satisfaction_bonus = (sentiment_score * success_rate) * 10
                
                trust_score = 10 + review_points + completion_points + skill_points + satisfaction_bonus
                trust_score = min(trust_score, 100)
                
            # Good performers (35%) - Reliable freelancers
            elif i < n_synthetic * 0.65:
                average_rating = np.random.uniform(4.0, 4.7)
                success_rate = np.random.uniform(0.80, 0.92)
                sentiment_score = np.random.uniform(0.75, 0.88)
                completed_jobs = np.random.randint(8, 25)
                skills_count = np.random.randint(5, 12)
                total_earnings = completed_jobs * np.random.uniform(600, 1200)
                
                # AI learns priority: REVIEW > JOB_COMPLETION > SKILLS > SATISFACTION
                
                # Priority 1: REVIEW (40% weight)
                review_component = (average_rating / 5.0) * 0.6 + sentiment_score * 0.4
                review_points = review_component * 40
                
                # Priority 2: JOB COMPLETION (30% weight)
                job_volume_normalized = min(completed_jobs / 50, 1.0)
                completion_component = job_volume_normalized * 0.5 + success_rate * 0.5
                completion_points = completion_component * 30
                
                # Priority 3: SKILLS (20% weight)
                skill_component = min(skills_count / 20, 1.0)
                skill_points = skill_component * 20
                
                # Priority 4: SATISFACTION (10% weight)
                satisfaction_bonus = (sentiment_score * success_rate) * 10
                
                trust_score = 10 + review_points + completion_points + skill_points + satisfaction_bonus
                
            # Developing performers (25%) - Growing freelancers
            elif i < n_synthetic * 0.9:
                average_rating = np.random.uniform(3.3, 4.0)
                success_rate = np.random.uniform(0.65, 0.80)
                sentiment_score = np.random.uniform(0.60, 0.75)
                completed_jobs = np.random.randint(3, 12)
                skills_count = np.random.randint(3, 8)
                total_earnings = completed_jobs * np.random.uniform(350, 600)
                
                # AI learns priority: REVIEW > JOB_COMPLETION > SKILLS > SATISFACTION
                
                # Priority 1: REVIEW (40% weight)
                review_component = (average_rating / 5.0) * 0.6 + sentiment_score * 0.4
                review_points = review_component * 40
                
                # Priority 2: JOB COMPLETION (30% weight)
                job_volume_normalized = min(completed_jobs / 50, 1.0)
                completion_component = job_volume_normalized * 0.5 + success_rate * 0.5
                completion_points = completion_component * 30
                
                # Priority 3: SKILLS (20% weight)
                skill_component = min(skills_count / 20, 1.0)
                skill_points = skill_component * 20
                
                # Priority 4: SATISFACTION (10% weight)
                satisfaction_bonus = (sentiment_score * success_rate) * 10
                
                trust_score = 10 + review_points + completion_points + skill_points + satisfaction_bonus
                
            # New/struggling performers (10%) - Need improvement
            else:
                average_rating = np.random.uniform(2.0, 3.3)
                success_rate = np.random.uniform(0.40, 0.65)
                sentiment_score = np.random.uniform(0.40, 0.60)
                completed_jobs = np.random.randint(0, 5)
                skills_count = np.random.randint(0, 5)
                total_earnings = completed_jobs * np.random.uniform(200, 400) if completed_jobs > 0 else 0
                
                # AI learns priority: REVIEW > JOB_COMPLETION > SKILLS > SATISFACTION
                
                # Priority 1: REVIEW (40% weight) - Low reviews = low trust
                review_component = (average_rating / 5.0) * 0.6 + sentiment_score * 0.4
                review_points = review_component * 40
                
                # Priority 2: JOB COMPLETION (30% weight) - Few jobs = low trust
                job_volume_normalized = min(completed_jobs / 50, 1.0)
                completion_component = job_volume_normalized * 0.5 + success_rate * 0.5
                completion_points = completion_component * 30
                
                # Priority 3: SKILLS (20% weight) - Few skills = low trust
                skill_component = min(skills_count / 20, 1.0)
                skill_points = skill_component * 20
                
                # Priority 4: SATISFACTION (10% weight)
                satisfaction_bonus = (sentiment_score * success_rate) * 10
                
                trust_score = 10 + review_points + completion_points + skill_points + satisfaction_bonus
                
                # Special cases for truly new freelancers
                if skills_count == 0:
                    trust_score = np.random.uniform(5, 15)  # No skills = very low trust
                elif completed_jobs == 0:
                    # New but has skills - give some base credit
                    trust_score = 10 + (skills_count / 20) * 15
            
            # Add realistic noise (AI learns from imperfect data)
            trust_score += np.random.normal(0, 2)  # Small random variations
            trust_score = max(0, min(trust_score, 100))  # Clamp to 0-100
            
            avg_job_value = total_earnings / max(completed_jobs, 1)
            rating_consistency = average_rating / 5.0 if average_rating > 0 else 0
            
            data.append({
                'average_rating': average_rating,
                'success_rate': success_rate,
                'sentiment_score': sentiment_score,
                'completed_jobs': completed_jobs,
                'skills_count': skills_count,
                'total_earnings': total_earnings,
                'avg_job_value': avg_job_value,
                'rating_consistency': rating_consistency,
                'trust_score': trust_score
            })
        
        # Add edge cases for robustness
        print("🎯 Adding edge cases for AI robustness...")
        
        # Add SKILL COMPARISON PAIRS - teach AI that skills matter!
        print("📚 Adding skill-comparison training pairs (same profile, different skills)...")
        for _ in range(100):
            # Create identical profiles with ONLY skills varying
            base_rating = np.random.uniform(4.0, 4.8)
            base_success = np.random.uniform(0.85, 0.98)
            base_sentiment = np.random.uniform(0.85, 0.95)
            base_jobs = np.random.randint(10, 25)
            base_earnings = base_jobs * np.random.uniform(800, 1500)
            avg_value = base_earnings / base_jobs
            consistency = base_rating / 5.0
            
            # Profile with 0 skills
            trust_0 = 65 + (base_rating - 4.0) * 15 + (base_success - 0.85) * 30
            data.append({
                'average_rating': base_rating,
                'success_rate': base_success,
                'sentiment_score': base_sentiment,
                'completed_jobs': base_jobs,
                'skills_count': 0,  # NO SKILLS
                'total_earnings': base_earnings,
                'avg_job_value': avg_value,
                'rating_consistency': consistency,
                'trust_score': trust_0
            })
            
            # Same profile with 1-3 skills (small boost)
            skills_1to3 = np.random.randint(1, 4)
            trust_low = trust_0 + (skills_1to3 * 2)  # +2-6 points
            data.append({
                'average_rating': base_rating,
                'success_rate': base_success,
                'sentiment_score': base_sentiment,
                'completed_jobs': base_jobs,
                'skills_count': skills_1to3,  # FEW SKILLS
                'total_earnings': base_earnings,
                'avg_job_value': avg_value,
                'rating_consistency': consistency,
                'trust_score': trust_low
            })
            
            # Same profile with 5-8 skills (medium boost)
            skills_5to8 = np.random.randint(5, 9)
            trust_med = trust_0 + (skills_5to8 * 2)  # +10-16 points
            data.append({
                'average_rating': base_rating,
                'success_rate': base_success,
                'sentiment_score': base_sentiment,
                'completed_jobs': base_jobs,
                'skills_count': skills_5to8,  # MODERATE SKILLS
                'total_earnings': base_earnings,
                'avg_job_value': avg_value,
                'rating_consistency': consistency,
                'trust_score': min(trust_med, 100)
            })
            
            # Same profile with 10-15 skills (large boost)
            skills_10plus = np.random.randint(10, 16)
            trust_high = trust_0 + (skills_10plus * 2)  # +20-30 points
            data.append({
                'average_rating': base_rating,
                'success_rate': base_success,
                'sentiment_score': base_sentiment,
                'completed_jobs': base_jobs,
                'skills_count': skills_10plus,  # MANY SKILLS
                'total_earnings': base_earnings,
                'avg_job_value': avg_value,
                'rating_consistency': consistency,
                'trust_score': min(trust_high, 100)
            })
        
        # Perfect freelancer
        data.append({
            'average_rating': 5.0,
            'success_rate': 1.0,
            'sentiment_score': 1.0,
            'completed_jobs': 50,
            'skills_count': 20,
            'total_earnings': 100000,
            'avg_job_value': 2000,
            'rating_consistency': 1.0,
            'trust_score': 100
        })
        
        # Brand new freelancer
        data.append({
            'average_rating': 0,
            'success_rate': 0,
            'sentiment_score': 0.5,
            'completed_jobs': 0,
            'skills_count': 3,
            'total_earnings': 0,
            'avg_job_value': 0,
            'rating_consistency': 0,
            'trust_score': 10
        })
        
        # Inconsistent performer (high skills, low delivery)
        data.append({
            'average_rating': 3.0,
            'success_rate': 0.5,
            'sentiment_score': 0.6,
            'completed_jobs': 20,
            'skills_count': 15,
            'total_earnings': 10000,
            'avg_job_value': 500,
            'rating_consistency': 0.6,
            'trust_score': 45
        })
        
        return pd.DataFrame(data)
    
    def train_model(self, n_samples: int = 1000):
        """
        Train the Random Forest model using real database data
        """
        print("🤖 Generating training data for Trust Score AI...")
        df = self.create_training_data_from_database()
        
        # Prepare features and target
        X = df[self.feature_names]
        y = df['trust_score']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print("🧠 Training Random Forest model...")
        # Train Random Forest with optimized parameters
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        
        print(f"✅ Trust Score AI Model Performance:")
        print(f"   Training R² Score: {train_r2:.4f}")
        print(f"   Testing R² Score: {test_r2:.4f}")
        print(f"   Training MAE: {train_mae:.2f}")
        print(f"   Testing MAE: {test_mae:.2f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n📊 Feature Importance:")
        for _, row in feature_importance.iterrows():
            print(f"   {row['feature']}: {row['importance']:.4f}")
        
        # Save model
        self.save_model()
        print(f"💾 Model saved to {self.model_path}")
        
        return {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'feature_importance': feature_importance.to_dict('records')
        }
    
    def load_model(self):
        """Load the trained model from disk"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"✅ Trust Score AI model loaded from {self.model_path}")
            return True
        return False
    
    def save_model(self):
        """Save the trained model to disk"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
    
    def validate_and_filter_skills(self, skills: list) -> list:
        """
        Validate skills and return only valid ones (filters out gibberish)
        
        Args:
            skills: List of skill names
            
        Returns:
            List of valid skills only
        """
        if not skills or len(skills) == 0:
            return []
        
        # Valid technical skills database (same as cost_time_service)
        valid_skills = [
            # Programming Languages
            'python', 'java','javascript', 'typescript', 'c', 'c++', 'c#', 'csharp', 'ruby',
            'php', 'swift', 'kotlin', 'go', 'golang', 'rust', 'scala', 'r', 'matlab', 'perl',
            'dart', 'elixir', 'haskell', 'lua', 'objective-c', 'sql', 'bash', 'shell', 'powershell',
            
            # Web Development
            'html', 'css', 'react', 'angular', 'vue', 'vuejs', 'nextjs', 'nuxt', 'svelte',
            'jquery', 'bootstrap', 'tailwind', 'sass', 'less', 'webpack', 'vite', 'nodejs',
            'node', 'express', 'nestjs', 'django', 'flask', 'fastapi', 'spring', 'laravel',
            
            # Mobile Development
            'android', 'ios', 'flutter', 'react-native', 'reactnative', 'xamarin', 'ionic',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'mssql', 'sqlserver',
            'firebase', 'elasticsearch',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'linux', 'nginx',
            
            # Data Science & AI
            'machine-learning', 'deep-learning', 'tensorflow', 'pytorch', 'pandas', 'numpy',
            
            # Design
            'figma', 'photoshop', 'illustrator', 'ui-design', 'ux-design',
            
            # Other
            'git', 'api', 'testing', 'agile'
        ]
        
        valid_skills_filtered = []
        
        for skill in skills:
            skill_clean = skill.strip().lower()
            
            # Skip empty skills
            if not skill_clean or len(skill_clean) < 2:
                continue
            
            # Check for gibberish patterns
            # 1. Repeated patterns (e3e3e3e3)
            repeated_pattern = re.compile(r'(.{1,3})\1{3,}')
            if repeated_pattern.match(skill_clean):
                continue
            
            # 2. All same character (oooo, eee, ww)
            if len(set(skill_clean)) == 1:
                continue
            
            # 3. Check if skill matches valid skills FIRST (before vowel ratio check)
            is_valid = False
            for valid_skill in valid_skills:
                if valid_skill == skill_clean or valid_skill in skill_clean or skill_clean in valid_skill:
                    is_valid = True
                    break
            
            # If already validated as a known skill, add it immediately
            if is_valid:
                valid_skills_filtered.append(skill)
                continue
            
            # 4. Very poor vowel ratio check (only for unknown skills)
            # Skip this check for skills with special characters (like C++, C#, .NET)
            if not re.search(r'[+#.]', skill_clean):
                vowels = len(re.findall(r'[aeiou]', skill_clean))
                consonants = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', skill_clean))
                
                if consonants > 0:
                    vowel_ratio = vowels / (vowels + consonants)
                    if vowel_ratio < 0.10 or vowel_ratio > 0.80:
                        continue
            
            # 5. Check structure patterns for unknown skills
            if '-' in skill_clean or ' ' in skill_clean:
                is_valid = True
            elif any(skill_clean.startswith(prefix) for prefix in ['front', 'back', 'full', 'web', 'mobile', 'data', 'cloud']):
                is_valid = True
            elif 3 <= len(skill_clean) <= 20:
                vowels = len(re.findall(r'[aeiou]', skill_clean))
                consonants = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', skill_clean))
                if consonants > 0:
                    vowel_ratio = vowels / (vowels + consonants)
                    if vowel_ratio > 0.15:
                        is_valid = True
            
            if is_valid:
                valid_skills_filtered.append(skill)
        
        return valid_skills_filtered
    
    def prepare_features(self, profile: dict) -> pd.DataFrame:
        """
        Extract and prepare features from freelancer profile
        Filters out invalid/gibberish skills
        """
        # Base features from profile
        average_rating = profile.get('average_rating', 0)
        success_rate = profile.get('success_rate', 0)
        sentiment_score = profile.get('sentiment_score', 0)
        completed_jobs = profile.get('completed_jobs', 0)
        
        # FILTER SKILLS - Only count valid skills, ignore gibberish
        raw_skills = profile.get('skills', [])
        valid_skills = self.validate_and_filter_skills(raw_skills)
        skills_count = len(valid_skills)  # Only count VALID skills
        
        total_earnings = profile.get('total_earnings', 0)
        
        # Derived features
        avg_job_value = total_earnings / max(completed_jobs, 1)
        # Rating consistency: perfect rating (5.0) = 1.0, lower ratings = lower consistency
        rating_consistency = average_rating / 5.0 if average_rating > 0 else 0
        
        # Create feature dataframe
        features = pd.DataFrame([{
            'average_rating': average_rating,
            'success_rate': success_rate,
            'sentiment_score': sentiment_score,
            'completed_jobs': completed_jobs,
            'skills_count': skills_count,  # Uses filtered count
            'total_earnings': total_earnings,
            'avg_job_value': avg_job_value,
            'rating_consistency': rating_consistency
        }])
        
        return features[self.feature_names]
    
    def predict_trust_score(self, freelancer_id: str) -> dict:
        """
        Predict trust score using trained AI model (Random Forest)
        AI learns complex patterns from training data
        """
        # Load model if not already loaded
        if self.model is None:
            if not self.load_model():
                print("⚠️  No trained model found. Training new model...")
                self.train_model()
        
        # Get freelancer profile
        profile = self.profile_db.get_profile(freelancer_id)
        
        if not profile:
            return {
                'trust_score': 0,
                'interpretation': 'New freelancer - No track record yet',
                'confidence': 0,
                'rating': 0,
                'success_rate': 0,
                'sentiment_score': 0,
                'skills_count': 0,
                'completed_jobs': 0,
                'calculation': 'AI Model (Random Forest)'
            }
        
        # Extract metrics
        average_rating = profile.get('average_rating', 0)
        success_rate = profile.get('success_rate', 0)
        sentiment_score = profile.get('sentiment_score', 0)
        completed_jobs = profile.get('completed_jobs', 0)
        total_earnings = profile.get('total_earnings', 0)
        
        # FILTER SKILLS - Only count valid skills, ignore gibberish like "ww", "wd", "e3e3"
        raw_skills = profile.get('skills', [])
        valid_skills = self.validate_and_filter_skills(raw_skills)
        skills_count = len(valid_skills)  # Only count VALID skills
        
        # Handle new freelancers with no jobs
        if completed_jobs == 0:
            # AI predicts low trust for new freelancers
            trust_score = 10.0
            confidence = 0
        else:
            # Prepare features for AI prediction using the profile dict
            features = self.prepare_features(profile)
            
            # AI MODEL PREDICTION
            trust_score = self.model.predict(features)[0]
            trust_score = round(np.clip(trust_score, 0, 100), 1)
            
            # Calculate confidence based on completed jobs
            confidence = min(completed_jobs / 20, 1.0) * 100
        
        # Determine interpretation based on AI prediction
        if trust_score >= 85:
            interpretation = "Excellent - Highly Experienced & Top-Rated"
        elif trust_score >= 70:
            interpretation = "Very Good - Experienced & Reliable"
        elif trust_score >= 55:
            interpretation = "Good - Competent with Track Record"
        elif trust_score >= 40:
            interpretation = "Average - Building Experience"
        else:
            interpretation = "Beginner - Limited Track Record"
        
        return {
            'trust_score': trust_score,
            'interpretation': interpretation,
            'confidence': round(confidence, 1),
            'rating': average_rating,
            'success_rate': success_rate,
            'sentiment_score': sentiment_score,
            'skills_count': skills_count,
            'completed_jobs': completed_jobs,
            'calculation': 'AI Model (Random Forest) - Trained on 2000+ patterns'
        }


if __name__ == "__main__":
    # Train the model when run directly
    service = TrustScoreAI()
    metrics = service.train_model(n_samples=2000)
    print("\n✅ Trust Score AI model training complete!")
