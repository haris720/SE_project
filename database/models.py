"""
Database models and collections for the freelancer marketplace
"""

from datetime import datetime
from typing import List, Dict, Optional
from database.db_connection import DatabaseConnection
from bson import ObjectId


class FreelancerProfile:
    """Freelancer profile management"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.collection = self.db.get_collection("freelancer_profiles")
    
    def create_profile(self, user_id: str, data: Dict) -> Dict:
        """Create freelancer profile"""
        profile = {
            'user_id': user_id,
            'skills': data.get('skills', []),
            'bio': data.get('bio', ''),
            'hourly_rate': data.get('hourly_rate', 0),
            'portfolio': data.get('portfolio', []),
            'completed_jobs': 0,
            'total_earnings': 0,
            'average_rating': 0.0,  # Starts at 0, updated by CLIENT ratings
            'success_rate': 0.0,  # Starts at 0%, updated by CLIENT feedback
            'total_reviews': 0,
            'sentiment_score': 0.0,  # Starts at 0%, updated by CLIENT ratings
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = self.collection.insert_one(profile)
        profile['_id'] = str(result.inserted_id)
        return profile
    
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Get freelancer profile by user_id"""
        profile = self.collection.find_one({'user_id': user_id})
        if profile:
            profile['_id'] = str(profile['_id'])
            # Convert datetime to string for JSON serialization
            if 'created_at' in profile:
                profile['created_at'] = profile['created_at'].isoformat()
            if 'updated_at' in profile:
                profile['updated_at'] = profile['updated_at'].isoformat()
        return profile
    
    def update_profile(self, user_id: str, data: Dict) -> bool:
        """Update freelancer profile"""
        data['updated_at'] = datetime.utcnow()
        result = self.collection.update_one(
            {'user_id': user_id},
            {'$set': data}
        )
        return result.modified_count > 0
    
    def update_after_job_completion(self, user_id: str, rating: float, success: bool):
        """Update profile metrics after job completion"""
        profile = self.get_profile(user_id)
        if not profile:
            return False
        
        # Update average rating (client provides rating 1-5)
        total_reviews = profile['total_reviews']
        current_avg = profile['average_rating']
        new_avg = ((current_avg * total_reviews) + rating) / (total_reviews + 1)
        
        # Update success rate (client marks if job was successful or not)
        completed = profile['completed_jobs']
        current_success_rate = profile['success_rate']
        
        # If this is first job, set success rate directly
        if completed == 0:
            new_success_rate = 1.0 if success else 0.0
        else:
            # Calculate: (successful jobs + new result) / (total jobs + 1)
            successful_jobs = int(completed * current_success_rate)
            if success:
                new_success_rate = (successful_jobs + 1) / (completed + 1)
            else:
                new_success_rate = successful_jobs / (completed + 1)
        
        # Update client satisfaction (sentiment) based on rating
        # Convert 5-star rating to 0-1 scale for sentiment
        sentiment = rating / 5.0
        current_sentiment = profile['sentiment_score']
        new_sentiment = ((current_sentiment * total_reviews) + sentiment) / (total_reviews + 1)
        
        self.collection.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'average_rating': round(new_avg, 2),
                    'success_rate': round(new_success_rate, 4),
                    'sentiment_score': round(new_sentiment, 4),
                    'updated_at': datetime.utcnow()
                },
                '$inc': {
                    'completed_jobs': 1,
                    'total_reviews': 1
                }
            }
        )
        return True
    
    def get_all_freelancers(self) -> List[Dict]:
        """Get all freelancer profiles"""
        profiles = list(self.collection.find())
        for profile in profiles:
            profile['_id'] = str(profile['_id'])
            if 'created_at' in profile:
                profile['created_at'] = profile['created_at'].isoformat()
            if 'updated_at' in profile:
                profile['updated_at'] = profile['updated_at'].isoformat()
        return profiles


class Job:
    """Job posting management"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.collection = self.db.get_collection("jobs")
    
    def create_job(self, client_id: str, data: Dict) -> Dict:
        """Create a new job posting"""
        job = {
            'client_id': client_id,
            'title': data['title'],
            'description': data['description'],
            'skills_required': data['skills_required'],
            'complexity': data.get('complexity', 'Moderate'),
            'budget_min': data.get('budget_min', 0),
            'budget_max': data.get('budget_max', 0),
            'estimated_cost': data.get('estimated_cost', 0),
            'estimated_days': data.get('estimated_days', 0),
            'status': 'open',  # open, in_progress, completed, cancelled
            'applications': [],
            'assigned_to': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = self.collection.insert_one(job)
        job['_id'] = str(result.inserted_id)
        return job
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        try:
            job = self.collection.find_one({'_id': ObjectId(job_id)})
            if job:
                job['_id'] = str(job['_id'])
                # Convert datetime fields
                if 'created_at' in job and job['created_at']:
                    job['created_at'] = job['created_at'].isoformat()
                if 'updated_at' in job and job['updated_at']:
                    job['updated_at'] = job['updated_at'].isoformat()
                if 'completed_at' in job and job['completed_at']:
                    job['completed_at'] = job['completed_at'].isoformat()
                if 'submitted_at' in job and job['submitted_at']:
                    job['submitted_at'] = job['submitted_at'].isoformat()
                # Convert application dates
                if 'applications' in job:
                    for app in job['applications']:
                        if 'applied_at' in app and app['applied_at']:
                            app['applied_at'] = app['applied_at'].isoformat()
                        if 'updated_at' in app and app['updated_at']:
                            app['updated_at'] = app['updated_at'].isoformat()
            return job
        except:
            return None
    
    def get_all_open_jobs(self) -> List[Dict]:
        """Get all open jobs"""
        jobs = list(self.collection.find({'status': 'open'}).sort('created_at', -1))
        for job in jobs:
            job['_id'] = str(job['_id'])
            # Convert datetime to string for JSON serialization
            if 'created_at' in job:
                job['created_at'] = job['created_at'].isoformat()
            if 'updated_at' in job:
                job['updated_at'] = job['updated_at'].isoformat()
            # Convert application dates
            if 'applications' in job:
                for app in job['applications']:
                    if 'applied_at' in app:
                        app['applied_at'] = app['applied_at'].isoformat()
        return jobs
    
    def get_client_jobs(self, client_id: str) -> List[Dict]:
        """Get all jobs posted by a client"""
        jobs = list(self.collection.find({'client_id': client_id}).sort('created_at', -1))
        for job in jobs:
            job['_id'] = str(job['_id'])
            if 'created_at' in job:
                job['created_at'] = job['created_at'].isoformat()
            if 'updated_at' in job:
                job['updated_at'] = job['updated_at'].isoformat()
            if 'completed_at' in job:
                job['completed_at'] = job['completed_at'].isoformat()
            if 'submitted_at' in job:
                job['submitted_at'] = job['submitted_at'].isoformat()
            # Convert application dates
            if 'applications' in job:
                for app in job['applications']:
                    if 'applied_at' in app:
                        app['applied_at'] = app['applied_at'].isoformat()
                    if 'updated_at' in app:
                        app['updated_at'] = app['updated_at'].isoformat()
        return jobs
    
    def apply_for_job(self, job_id: str, freelancer_id: str, proposal: str) -> bool:
        """Freelancer applies for a job - sends request to client"""
        try:
            application = {
                'freelancer_id': freelancer_id,
                'proposal': proposal,
                'applied_at': datetime.utcnow(),
                'status': 'pending'  # pending, accepted, rejected
            }
            result = self.collection.update_one(
                {'_id': ObjectId(job_id)},
                {
                    '$push': {'applications': application},
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except:
            return False
    
    def update_application_status(self, job_id: str, freelancer_id: str, status: str) -> bool:
        """Client accepts or rejects an application"""
        try:
            result = self.collection.update_one(
                {
                    '_id': ObjectId(job_id),
                    'applications.freelancer_id': freelancer_id
                },
                {
                    '$set': {
                        'applications.$.status': status,  # 'accepted' or 'rejected'
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except:
            return False
    
    def assign_job(self, job_id: str, freelancer_id: str) -> bool:
        """Client assigns job to a freelancer after accepting application"""
        try:
            result = self.collection.update_one(
                {'_id': ObjectId(job_id)},
                {
                    '$set': {
                        'assigned_to': freelancer_id,
                        'status': 'in_progress',
                        'work_submitted': False,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except:
            return False
    
    def submit_work(self, job_id: str, freelancer_id: str, submission_notes: str) -> bool:
        """Freelancer submits completed work to client"""
        try:
            result = self.collection.update_one(
                {
                    '_id': ObjectId(job_id),
                    'assigned_to': freelancer_id,
                    'status': 'in_progress'
                },
                {
                    '$set': {
                        'work_submitted': True,
                        'submission_notes': submission_notes,
                        'submitted_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except:
            return False
    
    def complete_job(self, job_id: str, rating: float, success: bool, review: str, payment: float = 0) -> bool:
        """Client marks job as completed and provides rating after work is submitted"""
        try:
            result = self.collection.update_one(
                {
                    '_id': ObjectId(job_id),
                    'work_submitted': True  # Can only complete if work was submitted
                },
                {
                    '$set': {
                        'status': 'completed',
                        'rating': rating,  # Client's rating 1-5
                        'success': success,  # True if job completed successfully
                        'review': review,  # Client's written review
                        'payment': payment,  # Amount paid to freelancer
                        'completed_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except:
            return False
    
    def get_freelancer_jobs(self, freelancer_id: str) -> List[Dict]:
        """Get all jobs assigned to a freelancer"""
        jobs = list(self.collection.find({'assigned_to': freelancer_id}).sort('created_at', -1))
        for job in jobs:
            job['_id'] = str(job['_id'])
            if 'created_at' in job:
                job['created_at'] = job['created_at'].isoformat()
            if 'updated_at' in job:
                job['updated_at'] = job['updated_at'].isoformat()
            if 'completed_at' in job:
                job['completed_at'] = job['completed_at'].isoformat()
            if 'submitted_at' in job:
                job['submitted_at'] = job['submitted_at'].isoformat()
            # Convert application dates
            if 'applications' in job:
                for app in job['applications']:
                    if 'applied_at' in app:
                        app['applied_at'] = app['applied_at'].isoformat()
                    if 'updated_at' in app:
                        app['updated_at'] = app['updated_at'].isoformat()
        return jobs
    
    def get_job_applications(self, freelancer_id: str) -> List[Dict]:
        """Get all jobs freelancer has applied to"""
        jobs = list(self.collection.find({
            'applications.freelancer_id': freelancer_id
        }).sort('created_at', -1))
        for job in jobs:
            job['_id'] = str(job['_id'])
            if 'created_at' in job:
                job['created_at'] = job['created_at'].isoformat()
            if 'updated_at' in job:
                job['updated_at'] = job['updated_at'].isoformat()
            if 'submitted_at' in job:
                job['submitted_at'] = job['submitted_at'].isoformat()
            # Convert application dates
            if 'applications' in job:
                for app in job['applications']:
                    if 'applied_at' in app:
                        app['applied_at'] = app['applied_at'].isoformat()
                    if 'updated_at' in app:
                        app['updated_at'] = app['updated_at'].isoformat()
        return jobs
