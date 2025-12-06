"""
Data Generation Script
Generates synthetic training data for freelancers and projects
"""

import random
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_connection import get_db_connection
from config import *


# Sample data for generation
SKILLS = [
    "Python", "JavaScript", "React", "Node.js", "Django", "Flask", "FastAPI",
    "Machine Learning", "Data Science", "MongoDB", "PostgreSQL", "MySQL",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "HTML", "CSS", "TypeScript",
    "Vue.js", "Angular", "Java", "C++", "Go", "Rust", "PHP", "Ruby",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "SQL",
    "GraphQL", "REST API", "Microservices", "DevOps", "CI/CD", "Git"
]

PROJECT_DESCRIPTIONS = [
    "Build a responsive e-commerce website with payment integration",
    "Develop a machine learning model for customer churn prediction",
    "Create a mobile app for task management and productivity",
    "Design and implement a RESTful API for social media platform",
    "Build a real-time chat application with WebSocket support",
    "Develop a data analytics dashboard with interactive visualizations",
    "Create an AI-powered recommendation system for products",
    "Build a content management system with user authentication",
    "Develop a booking system for hotels and restaurants",
    "Create a portfolio website with modern design and animations",
    "Build a custom CRM system for sales team management",
    "Develop a video streaming platform with adaptive bitrate",
    "Create an inventory management system with barcode scanning",
    "Build a learning management system for online courses",
    "Develop a marketplace platform connecting buyers and sellers",
    "Create a financial dashboard for investment portfolio tracking",
    "Build a job board platform with advanced search filters",
    "Develop a healthcare appointment scheduling system",
    "Create a social networking platform with user profiles",
    "Build an IoT dashboard for sensor data monitoring",
    "Develop a blog platform with SEO optimization",
    "Create a project management tool with Kanban boards",
    "Build a food delivery application with real-time tracking",
    "Develop a weather forecasting dashboard using ML models",
    "Create an automated email marketing system",
    "Build a cryptocurrency trading bot with backtesting",
    "Develop a document management system with version control",
    "Create a customer support ticketing system",
    "Build a subscription-based SaaS platform",
    "Develop a fitness tracking app with workout plans"
]

POSITIVE_REVIEWS = [
    "Excellent work! Delivered on time and exceeded expectations.",
    "Very professional and skilled developer. Highly recommended!",
    "Outstanding quality and great communication throughout the project.",
    "Perfect execution! Will definitely hire again.",
    "Amazing work ethic and technical skills. Very satisfied!",
    "Delivered exactly what was needed. Very reliable freelancer.",
    "Top-notch quality and fast delivery. Great experience!",
    "Very knowledgeable and helpful. Completed project flawlessly.",
    "Exceptional work! Went above and beyond requirements.",
    "Highly skilled and professional. Great to work with!"
]

NEUTRAL_REVIEWS = [
    "Good work overall. Some minor issues but resolved quickly.",
    "Decent quality. Met most requirements.",
    "Acceptable work. Communication could be better.",
    "Satisfactory results. Delivered on time.",
    "Good effort. A few revisions were needed.",
    "Fair quality. Project completed as requested.",
    "Reasonable work. Some delays but acceptable outcome.",
    "Average performance. Met basic expectations.",
    "Okay work. Nothing exceptional but gets the job done.",
    "Adequate quality. Would consider hiring again."
]

NEGATIVE_REVIEWS = [
    "Poor communication and multiple delays.",
    "Below expectations. Had to request many revisions.",
    "Unsatisfactory work quality. Not recommended.",
    "Missed deadlines and unclear deliverables.",
    "Disappointing results. Did not meet requirements.",
    "Lack of attention to detail. Many bugs in code.",
    "Unprofessional behavior and poor quality.",
    "Failed to deliver what was promised.",
    "Very slow response time and mediocre work.",
    "Not worth the money. Had to hire someone else to fix."
]

COMPLEXITY_LEVELS = ["Simple", "Moderate", "Complex", "Very Complex"]


def generate_sentiment_score(review_text: str) -> float:
    """Generate sentiment score based on review text"""
    if any(word in review_text.lower() for word in ["excellent", "outstanding", "amazing", "perfect", "exceptional"]):
        return round(random.uniform(0.7, 1.0), 2)
    elif any(word in review_text.lower() for word in ["poor", "disappointing", "unsatisfactory", "below"]):
        return round(random.uniform(0.0, 0.4), 2)
    else:
        return round(random.uniform(0.4, 0.7), 2)


def generate_freelancers(num_freelancers: int = 1000):
    """Generate synthetic freelancer data"""
    freelancers = []
    
    for i in range(num_freelancers):
        # Generate random metrics
        completed_jobs = random.randint(5, 200)
        success_rate = round(random.uniform(0.5, 1.0), 2)
        rating = round(random.uniform(2.0, 5.0), 1)
        
        # Select random skills (3-10 skills per freelancer)
        num_skills = random.randint(3, 10)
        freelancer_skills = random.sample(SKILLS, num_skills)
        
        # Generate reviews based on rating
        if rating >= 4.5:
            reviews = random.sample(POSITIVE_REVIEWS, min(3, len(POSITIVE_REVIEWS)))
        elif rating >= 3.5:
            reviews = random.sample(NEUTRAL_REVIEWS + POSITIVE_REVIEWS, 3)
        else:
            reviews = random.sample(NEGATIVE_REVIEWS + NEUTRAL_REVIEWS, 3)
        
        # Calculate average sentiment
        sentiments = [generate_sentiment_score(review) for review in reviews]
        avg_sentiment = round(np.mean(sentiments), 2)
        
        # Calculate trust score (ground truth for training)
        trust_score = round(
            (rating / 5.0) * 30 +
            success_rate * 25 +
            avg_sentiment * 20 +
            min(num_skills / 10, 1) * 15 +
            min(completed_jobs / 100, 1) * 10,
            1
        )
        trust_score = max(0, min(100, trust_score))  # Clamp between 0-100
        
        freelancer = {
            "freelancer_id": f"FL{i+1:05d}",
            "name": f"Freelancer {i+1}",
            "rating": rating,
            "success_rate": success_rate,
            "completed_jobs": completed_jobs,
            "skills": freelancer_skills,
            "skills_count": num_skills,
            "reviews": reviews,
            "sentiment_score": avg_sentiment,
            "trust_score": trust_score,
            "created_at": datetime.now() - timedelta(days=random.randint(30, 1000))
        }
        
        freelancers.append(freelancer)
    
    return freelancers


def generate_projects(num_projects: int = 800):
    """Generate synthetic project data"""
    projects = []
    
    for i in range(num_projects):
        # Select random project details
        description = random.choice(PROJECT_DESCRIPTIONS)
        complexity = random.choice(COMPLEXITY_LEVELS)
        
        # Select random skills (2-8 skills per project)
        num_skills = random.randint(2, 8)
        project_skills = random.sample(SKILLS, num_skills)
        
        # Generate cost based on complexity with 15% increments
        # Base costs: Simple -> Moderate (+15%) -> Complex (+15%) -> Very Complex (+15%)
        base_simple = 500  # Lower base cost for simple project
        
        complexity_multipliers = {
            "Simple": 1.0,
            "Moderate": 1.15,       # 15% more than Simple
            "Complex": 1.3225,      # 15% more than Moderate (1.15 * 1.15)
            "Very Complex": 1.520875  # 15% more than Complex (1.3225 * 1.15)
        }
        
        # Skill complexity adds less cost (each skill adds 3% instead of 5%)
        skill_multiplier = 1 + (num_skills * 0.03)
        
        # Calculate cost based on complexity and skills
        base_project_cost = base_simple * complexity_multipliers[complexity] * skill_multiplier
        
        # Add description-based variation (±5% for description complexity)
        description_variation = random.uniform(0.95, 1.05)
        actual_cost = int(base_project_cost * description_variation)
        
        # Calculate range around actual cost
        min_cost = int(actual_cost * 0.9)
        max_cost = int(actual_cost * 1.1)
        
        # Generate delivery time based on complexity with 15% increments
        # Base days for simple project with skills influence
        base_days_simple = 7  # Base for simple project
        
        # Apply same complexity multipliers as cost (15% increments)
        base_delivery = base_days_simple * complexity_multipliers[complexity]
        
        # Skills increase delivery time (each skill adds 5% to delivery time)
        skill_time_multiplier = 1 + (num_skills * 0.05)
        
        # Calculate final delivery days
        delivery_days = int(base_delivery * skill_time_multiplier * random.uniform(0.95, 1.05))
        delivery_days = max(1, delivery_days)  # At least 1 day
        
        project = {
            "project_id": f"PRJ{i+1:05d}",
            "title": f"Project {i+1}",
            "description": description,
            "complexity": complexity,
            "skills_required": project_skills,
            "skills_count": num_skills,
            "min_cost": min_cost,
            "max_cost": max_cost,
            "actual_cost": actual_cost,
            "delivery_days": delivery_days,
            "status": random.choice(["Completed", "Completed", "Completed", "In Progress"]),
            "created_at": datetime.now() - timedelta(days=random.randint(1, 365))
        }
        
        projects.append(project)
    
    return projects


def populate_database():
    """Populate MongoDB with generated data"""
    try:
        db = get_db_connection()
        
        print("🚀 Starting data generation...")
        
        # Clear existing data
        print("\n📦 Clearing existing collections...")
        db.clear_collection(FREELANCERS_COLLECTION)
        db.clear_collection(PROJECTS_COLLECTION)
        
        # Generate and insert freelancers
        print("\n👥 Generating freelancer data...")
        freelancers = generate_freelancers(1000)
        db.insert_many_freelancers(freelancers)
        print(f"✓ Inserted {len(freelancers)} freelancers")
        
        # Generate and insert projects
        print("\n📋 Generating project data...")
        projects = generate_projects(800)
        db.insert_many_projects(projects)
        print(f"✓ Inserted {len(projects)} projects")
        
        # Verify data
        print("\n✅ Data population complete!")
        print(f"   Total freelancers: {db.count_freelancers()}")
        print(f"   Total projects: {db.count_projects()}")
        
        # Show sample data
        print("\n📊 Sample Freelancer:")
        sample_freelancer = freelancers[0]
        print(f"   ID: {sample_freelancer['freelancer_id']}")
        print(f"   Rating: {sample_freelancer['rating']}")
        print(f"   Success Rate: {sample_freelancer['success_rate']}")
        print(f"   Trust Score: {sample_freelancer['trust_score']}")
        print(f"   Skills: {', '.join(sample_freelancer['skills'][:3])}")
        
        print("\n📊 Sample Project:")
        sample_project = projects[0]
        print(f"   ID: {sample_project['project_id']}")
        print(f"   Complexity: {sample_project['complexity']}")
        print(f"   Cost Range: ${sample_project['min_cost']} - ${sample_project['max_cost']}")
        print(f"   Delivery: {sample_project['delivery_days']} days")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        return False


if __name__ == "__main__":
    populate_database()
