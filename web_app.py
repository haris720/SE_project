"""
Web Application for AI Freelancer Evaluation System
Provides a user-friendly interface for freelancers and clients
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime
import uvicorn
import sys
import os
from bson import ObjectId

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web.auth import AuthService
from database.models import FreelancerProfile, Job
from services.trust_score_ai import TrustScoreAI
from services.cost_time_service import CostTimeEstimationService

# Create FastAPI app for web interface
web_app = FastAPI(title="AI Freelancer Evaluation - Web Interface")

# Initialize authentication service
auth_service = AuthService()
freelancer_profile_db = FreelancerProfile()
job_db = Job()
trust_score_ai = TrustScoreAI()
cost_service = CostTimeEstimationService()

# Load AI models on startup
try:
    cost_service.load_models()
    trust_score_ai.load_model()
    print("✅ AI models loaded successfully")
except Exception as e:
    print(f"⚠️  Warning: Could not load AI models: {e}")
    print("   Training models now...")
    try:
        trust_score_ai.train_model(n_samples=2000)
        print("✅ Trust Score AI model trained successfully")
    except Exception as train_error:
        print(f"❌ Error training model: {train_error}")

# Pydantic models for request validation
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    user_type: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileRequest(BaseModel):
    skills: List[str]
    bio: str
    hourly_rate: float
    portfolio: List[str] = []

class JobRequest(BaseModel):
    title: str
    description: str
    skills_required: List[str]
    complexity: str
    budget_min: float = 0
    budget_max: float = 0
    estimated_cost: float = 0
    estimated_days: int = 0

class JobApplicationRequest(BaseModel):
    job_id: str
    proposal: str
    cover_letter: str = ""
    proposed_budget: float = 0
    proposed_timeline: int = 0
    additional_notes: str = ""

class JobCompletionRequest(BaseModel):
    job_id: str
    rating: float  # 1-5 stars from client
    success: bool  # True if job was completed successfully
    review: str  # Client's written review
    final_price: float  # Final payment amount

class SubmitWorkRequest(BaseModel):
    job_id: str
    submission_notes: str
    deliverable_url: str = ""
    additional_comments: str = ""

class DirectJobRequest(BaseModel):
    freelancer_id: str
    title: str
    description: str
    complexity: str = "Moderate"
    skills_required: List[str] = []
    estimated_cost: float
    estimated_days: int
    additional_notes: str = ""

# Mount static files
web_app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="web/templates")

# Add CORS middleware
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@web_app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to signup page"""
    return RedirectResponse(url="/signup")


@web_app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page"""
    return templates.TemplateResponse("signup.html", {"request": request})


@web_app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@web_app.get("/freelancer-dashboard", response_class=HTMLResponse)
async def freelancer_dashboard(request: Request):
    """Freelancer dashboard page"""
    return templates.TemplateResponse("freelancer_dashboard_new.html", {"request": request})


@web_app.get("/client-dashboard", response_class=HTMLResponse)
async def client_dashboard(request: Request):
    """Client dashboard page"""
    return templates.TemplateResponse("client_dashboard_new.html", {"request": request})


@web_app.get("/proposal", response_class=HTMLResponse)
async def proposal_page(request: Request):
    """Proposal writing page for freelancers"""
    return templates.TemplateResponse("proposal_page.html", {"request": request})


@web_app.get("/submit-work", response_class=HTMLResponse)
async def submit_work_page(request: Request):
    """Work submission page for freelancers"""
    return templates.TemplateResponse("submit_work_page.html", {"request": request})


@web_app.get("/complete-order", response_class=HTMLResponse)
async def complete_order_page(request: Request):
    """Order completion and review page for clients"""
    return templates.TemplateResponse("complete_order_page.html", {"request": request})


@web_app.get("/request-freelancer", response_class=HTMLResponse)
async def request_freelancer_page(request: Request):
    """Request freelancer page for clients to send direct job requests"""
    return templates.TemplateResponse("request_freelancer_page.html", {"request": request})


# API Endpoints for Authentication
@web_app.post("/api/signup")
async def signup(data: SignupRequest):
    """Handle user signup"""
    result = auth_service.signup(
        email=data.email,
        password=data.password,
        user_type=data.user_type,
        name=data.name
    )
    return JSONResponse(content=result)


@web_app.post("/api/login")
async def login(data: LoginRequest):
    """Handle user login"""
    result = auth_service.login(
        email=data.email,
        password=data.password
    )
    return JSONResponse(content=result)


@web_app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Get user details by ID"""
    try:
        user = auth_service.users_collection.find_one({'_id': ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
            # Remove password from response
            user.pop('password', None)
            return JSONResponse(content={'success': True, 'user': user})
        return JSONResponse(content={'success': False, 'message': 'User not found'}, status_code=404)
    except Exception as e:
        return JSONResponse(content={'success': False, 'message': str(e)}, status_code=400)


# Freelancer Profile Endpoints
@web_app.post("/api/freelancer/profile")
async def create_or_update_profile(data: ProfileRequest, request: Request):
    """Create or update freelancer profile with skill validation"""
    # Get user_id from request (in real app, use JWT token)
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    # VALIDATE SKILLS - Reject invalid/gibberish skills
    if data.skills:
        skills_validation = cost_service.validate_skills(data.skills)
        if not skills_validation['valid']:
            return JSONResponse(content={
                'success': False, 
                'message': skills_validation['message']
            }, status_code=400)
    
    existing = freelancer_profile_db.get_profile(user_id)
    if existing:
        success = freelancer_profile_db.update_profile(user_id, data.model_dump())
        message = 'Profile updated'
    else:
        profile = freelancer_profile_db.create_profile(user_id, data.model_dump())
        # Remove datetime objects for JSON serialization
        if '_id' in profile:
            profile.pop('created_at', None)
            profile.pop('updated_at', None)
        success = True
        message = 'Profile created'
    
    if success:
        # Retrain Trust Score AI model with updated profile data
        print("🔄 Retraining Trust Score AI with updated profile...")
        try:
            trust_score_ai.train_model(n_samples=2000)
            print("✅ Trust Score AI retrained successfully")
        except Exception as e:
            print(f"⚠️ Trust Score AI retraining failed: {e}")
    
    return JSONResponse(content={'success': success, 'message': message})


@web_app.get("/api/freelancer/profile/{user_id}")
async def get_profile(user_id: str):
    """Get freelancer profile"""
    profile = freelancer_profile_db.get_profile(user_id)
    if profile:
        return JSONResponse(content={'success': True, 'profile': profile})
    return JSONResponse(content={'success': False, 'message': 'Profile not found'}, status_code=404)


@web_app.get("/api/freelancer/trust-score/{user_id}")
async def get_trust_score(user_id: str):
    """Get calculated trust score for freelancer"""
    score_data = trust_score_ai.predict_trust_score(user_id)
    return JSONResponse(content={'success': True, 'data': score_data})


# Job Endpoints
@web_app.post("/api/jobs/estimate")
async def estimate_job_cost(data: JobRequest, request: Request):
    """Get AI estimation for job cost and timeline without posting"""
    client_id = request.headers.get('X-User-ID')
    if not client_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    try:
        # Check if models are loaded
        if cost_service.cost_model is None or cost_service.time_model is None:
            return JSONResponse(content={
                'success': False, 
                'message': 'AI models not loaded. Please contact administrator.'
            }, status_code=503)
        
        project_data = {
            'description': data.description,
            'skills_required': data.skills_required,
            'complexity': data.complexity
        }
        prediction = cost_service.predict_cost_and_time(project_data)
        
        # Check if validation failed (description was gibberish/invalid)
        if prediction.get('error'):
            return JSONResponse(content={
                'success': False,
                'message': prediction['message']
            }, status_code=400)
        
        return JSONResponse(content={
            'success': True,
            'estimated_cost': prediction['estimated_cost'],
            'delivery_days': prediction['delivery_days'],
            'min_cost': prediction['min_cost'],
            'max_cost': prediction['max_cost']
        })
    except Exception as e:
        return JSONResponse(content={'success': False, 'message': f'Estimation failed: {str(e)}'}, status_code=500)


@web_app.post("/api/jobs/manual")
async def create_job_manual(data: JobRequest, request: Request):
    """Client creates job with manual budget and timeline"""
    client_id = request.headers.get('X-User-ID')
    if not client_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    try:
        data_dict = data.model_dump()
        job = job_db.create_job(client_id, data_dict)
        
        return JSONResponse(content={
            'success': True,
            'message': 'Job posted successfully',
            'job_id': job['_id']
        })
    except Exception as e:
        return JSONResponse(content={'success': False, 'message': str(e)}, status_code=500)


@web_app.post("/api/jobs")
async def create_job(data: JobRequest, request: Request):
    """Client creates a new job posting with AI estimation"""
    client_id = request.headers.get('X-User-ID')
    if not client_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    # Get AI cost estimate
    try:
        project_data = {
            'description': data.description,
            'skills_required': data.skills_required,
            'complexity': data.complexity
        }
        prediction = cost_service.predict_cost_and_time(project_data)
        
        # Check if validation failed (description was gibberish/invalid)
        if prediction.get('error'):
            return JSONResponse(content={
                'success': False,
                'message': prediction['message']
            }, status_code=400)
        
        data_dict = data.model_dump()
        data_dict['estimated_cost'] = prediction['estimated_cost']
        data_dict['estimated_days'] = prediction['delivery_days']
        data_dict['budget_min'] = prediction['min_cost']
        data_dict['budget_max'] = prediction['max_cost']
    except:
        data_dict = data.model_dump()
    
    job = job_db.create_job(client_id, data_dict)
    # Remove datetime for JSON
    job.pop('created_at', None)
    job.pop('updated_at', None)
    return JSONResponse(content={'success': True, 'message': 'Job posted successfully', 'job': job})


@web_app.get("/api/jobs")
async def get_all_jobs():
    """Get all open jobs"""
    jobs = job_db.get_all_open_jobs()
    return JSONResponse(content={'success': True, 'jobs': jobs})


@web_app.get("/api/jobs/{job_id}")
async def get_job_by_id(job_id: str, request: Request):
    """Get a specific job by ID"""
    user_id = request.headers.get('X-User-ID')
    try:
        job = job_db.get_job(job_id)
        if job:
            return JSONResponse(content={'success': True, 'job': job})
        return JSONResponse(content={'success': False, 'message': 'Job not found'}, status_code=404)
    except Exception as e:
        return JSONResponse(content={'success': False, 'message': str(e)}, status_code=400)


@web_app.get("/api/jobs/client/{client_id}")
async def get_client_jobs(client_id: str):
    """Get jobs posted by a client"""
    jobs = job_db.get_client_jobs(client_id)
    return JSONResponse(content={'success': True, 'jobs': jobs})


@web_app.get("/api/jobs/freelancer/{freelancer_id}")
async def get_freelancer_jobs(freelancer_id: str):
    """Get jobs assigned to a freelancer"""
    jobs = job_db.get_freelancer_jobs(freelancer_id)
    return JSONResponse(content={'success': True, 'jobs': jobs})


@web_app.post("/api/jobs/{job_id}/apply")
async def apply_for_job_with_proposal(job_id: str, request: Request, 
                                       cover_letter: str = "", 
                                       proposed_budget: float = 0,
                                       proposed_timeline: int = 0,
                                       additional_notes: str = ""):
    """Freelancer applies for a job with detailed proposal"""
    freelancer_id = request.headers.get('X-User-ID')
    if not freelancer_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    # Get request body
    body = await request.json()
    cover_letter = body.get('cover_letter', '')
    proposed_budget = body.get('proposed_budget', 0)
    proposed_timeline = body.get('proposed_timeline', 0)
    additional_notes = body.get('additional_notes', '')
    
    # Create proposal text
    proposal = f"Cover Letter:\n{cover_letter}\n\nProposed Budget: ${proposed_budget}\nProposed Timeline: {proposed_timeline} days"
    if additional_notes:
        proposal += f"\n\nAdditional Notes:\n{additional_notes}"
    
    success = job_db.apply_for_job(job_id, freelancer_id, proposal)
    if success:
        return JSONResponse(content={'success': True, 'message': 'Application sent to client! Wait for approval.'})
    return JSONResponse(content={'success': False, 'message': 'Failed to apply'}, status_code=400)


@web_app.post("/api/jobs/application/{job_id}/{freelancer_id}/{action}")
async def handle_application(job_id: str, freelancer_id: str, action: str):
    """Client accepts or rejects a freelancer application"""
    if action not in ['accept', 'reject']:
        return JSONResponse(content={'success': False, 'message': 'Invalid action'}, status_code=400)
    
    # Update application status
    status = 'accepted' if action == 'accept' else 'rejected'
    success = job_db.update_application_status(job_id, freelancer_id, status)
    
    if not success:
        return JSONResponse(content={'success': False, 'message': 'Failed to update application'}, status_code=400)
    
    # If accepted, assign the job to freelancer
    if action == 'accept':
        job_db.assign_job(job_id, freelancer_id)
        return JSONResponse(content={'success': True, 'message': 'Application accepted! Job assigned to freelancer.'})
    else:
        return JSONResponse(content={'success': True, 'message': 'Application rejected.'})


@web_app.post("/api/jobs/{job_id}/submit-work")
async def submit_work_detailed(job_id: str, request: Request):
    """Freelancer submits completed work to client with detailed information"""
    freelancer_id = request.headers.get('X-User-ID')
    if not freelancer_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    # Get request body
    body = await request.json()
    submission_notes = body.get('submission_notes', '')
    deliverable_url = body.get('deliverable_url', '')
    additional_comments = body.get('additional_comments', '')
    
    # Create full submission notes
    full_notes = submission_notes
    if deliverable_url:
        full_notes = f"Deliverable URL: {deliverable_url}\n\n{submission_notes}"
    if additional_comments:
        full_notes += f"\n\nAdditional Comments:\n{additional_comments}"
    
    # Store deliverable URL separately in job
    job = job_db.get_job(job_id)
    if job:
        job_db.collection.update_one(
            {'_id': ObjectId(job_id)},
            {'$set': {'deliverable_url': deliverable_url}}
        )
    
    success = job_db.submit_work(job_id, freelancer_id, full_notes)
    if success:
        return JSONResponse(content={'success': True, 'message': 'Work submitted! Client will review and complete the order.'})
    return JSONResponse(content={'success': False, 'message': 'Failed to submit work'}, status_code=400)


@web_app.post("/api/jobs/assign/{job_id}/{freelancer_id}")
async def assign_job(job_id: str, freelancer_id: str):
    """Client assigns job to freelancer"""
    success = job_db.assign_job(job_id, freelancer_id)
    if success:
        return JSONResponse(content={'success': True, 'message': 'Job assigned successfully'})
    return JSONResponse(content={'success': False, 'message': 'Failed to assign job'}, status_code=400)


@web_app.post("/api/jobs/{job_id}/complete")
async def complete_job_with_review(job_id: str, request: Request):
    """Client marks order as complete and provides rating after freelancer submits work"""
    client_id = request.headers.get('X-User-ID')
    if not client_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    # Get request body
    body = await request.json()
    rating = body.get('rating', 0)
    review = body.get('review', '')
    success = body.get('success', True)
    final_price = body.get('final_price', 0)
    
    # Get job details
    job = job_db.get_job(job_id)
    if not job:
        return JSONResponse(content={'success': False, 'message': 'Job not found'}, status_code=404)
    
    # Check if work was submitted
    if not job.get('work_submitted'):
        return JSONResponse(content={'success': False, 'message': 'Cannot complete: Freelancer has not submitted work yet'}, status_code=400)
    
    # Mark job as complete with client's feedback
    job_success = job_db.complete_job(
        job_id, 
        rating,  # Client's rating (1-5 stars)
        success,  # Did freelancer complete successfully?
        review,   # Client's written review
        final_price   # Final payment amount
    )
    
    if job_success and job.get('assigned_to'):
        # Automatically update freelancer's profile metrics based on client feedback
        # This updates: average_rating, success_rate, and client_satisfaction (sentiment)
        freelancer_profile_db.update_after_job_completion(
            job['assigned_to'],
            rating,   # Client's rating determines satisfaction score
            success   # Client's success marking affects success rate
        )
        
        # Update freelancer earnings
        if final_price > 0:
            freelancer_profile_db.collection.update_one(
                {'user_id': job['assigned_to']},
                {'$inc': {'total_earnings': final_price}}
            )
        
        # Retrain Trust Score AI model with new review data
        print("🔄 Retraining Trust Score AI with new client review...")
        try:
            trust_score_ai.train_model(n_samples=2000)
            print("✅ Trust Score AI retrained successfully")
        except Exception as e:
            print(f"⚠️ Trust Score AI retraining failed: {e}")
        
        return JSONResponse(content={
            'success': True, 
            'message': 'Order completed! Freelancer has been rated and paid.'
        })
    
    return JSONResponse(content={'success': False, 'message': 'Failed to complete job'}, status_code=400)


@web_app.get("/api/freelancers/search")
async def search_freelancers(skill: str = None):
    """Search freelancers by skill and return sorted by trust score"""
    try:
        # Get all freelancer profiles
        if skill:
            # Search by skill (case-insensitive)
            profiles = list(freelancer_profile_db.collection.find({
                'skills': {'$regex': skill, '$options': 'i'}
            }))
        else:
            profiles = list(freelancer_profile_db.collection.find())
        
        # Calculate trust score for each and sort
        freelancers_with_scores = []
        for profile in profiles:
            user_id = profile['user_id']
            trust_data = trust_score_ai.predict_trust_score(user_id)
            
            freelancers_with_scores.append({
                'user_id': user_id,
                'skills': profile.get('skills', []),
                'bio': profile.get('bio', ''),
                'hourly_rate': profile.get('hourly_rate', 0),
                'completed_jobs': profile.get('completed_jobs', 0),
                'average_rating': profile.get('average_rating', 0),
                'trust_score': trust_data.get('trust_score', 0),
                'success_rate': trust_data.get('success_rate', 0),
                'sentiment_score': trust_data.get('sentiment_score', 0)
            })
        
        # Sort by trust score (highest first)
        freelancers_with_scores.sort(key=lambda x: x['trust_score'], reverse=True)
        
        return JSONResponse(content={
            'success': True,
            'freelancers': freelancers_with_scores
        })
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'message': f'Search failed: {str(e)}'
        }, status_code=500)


@web_app.post("/api/jobs/direct-request")
async def send_direct_job_request(data: DirectJobRequest, request: Request):
    """Client sends a direct job request to a specific freelancer"""
    client_id = request.headers.get('X-User-ID')
    if not client_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    try:
        # Create job with direct request to specific freelancer
        job = {
            'title': data.title,
            'description': data.description,
            'client_id': client_id,
            'estimated_cost': data.estimated_cost,
            'estimated_days': data.estimated_days,
            'budget_min': data.estimated_cost * 0.8,
            'budget_max': data.estimated_cost * 1.2,
            'skills_required': [],
            'status': 'pending_acceptance',  # New status for direct requests
            'requested_freelancer': data.freelancer_id,  # Specific freelancer requested
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = job_db.collection.insert_one(job)
        
        return JSONResponse(content={
            'success': True,
            'message': 'Job request sent to freelancer! Waiting for their acceptance.',
            'job_id': str(result.inserted_id)
        })
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'message': f'Failed to send request: {str(e)}'
        }, status_code=500)


@web_app.get("/api/jobs/requests/{freelancer_id}")
async def get_job_requests(freelancer_id: str):
    """Get all direct job requests for a freelancer"""
    try:
        jobs = list(job_db.collection.find({
            'requested_freelancer': freelancer_id,
            'status': 'pending_acceptance'
        }).sort('created_at', -1))
        
        for job in jobs:
            job['_id'] = str(job['_id'])
            if 'created_at' in job:
                job['created_at'] = job['created_at'].isoformat()
            if 'updated_at' in job:
                job['updated_at'] = job['updated_at'].isoformat()
        
        return JSONResponse(content={'success': True, 'requests': jobs})
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'message': f'Failed to load requests: {str(e)}'
        }, status_code=500)


@web_app.post("/api/jobs/accept-request/{job_id}")
async def accept_job_request(job_id: str, request: Request):
    """Freelancer accepts a direct job request from client"""
    freelancer_id = request.headers.get('X-User-ID')
    if not freelancer_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    try:
        result = job_db.collection.update_one(
            {
                '_id': ObjectId(job_id),
                'requested_freelancer': freelancer_id,
                'status': 'pending_acceptance'
            },
            {
                '$set': {
                    'status': 'in_progress',
                    'assigned_to': freelancer_id,
                    'work_submitted': False,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return JSONResponse(content={
                'success': True,
                'message': 'Job request accepted! You can now start working on it.'
            })
        else:
            return JSONResponse(content={
                'success': False,
                'message': 'Request not found or already processed'
            }, status_code=404)
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'message': f'Failed to accept request: {str(e)}'
        }, status_code=500)


@web_app.post("/api/jobs/reject-request/{job_id}")
async def reject_job_request(job_id: str, request: Request):
    """Freelancer rejects a direct job request from client"""
    freelancer_id = request.headers.get('X-User-ID')
    if not freelancer_id:
        return JSONResponse(content={'success': False, 'message': 'User ID required'}, status_code=400)
    
    try:
        result = job_db.collection.update_one(
            {
                '_id': ObjectId(job_id),
                'requested_freelancer': freelancer_id,
                'status': 'pending_acceptance'
            },
            {
                '$set': {
                    'status': 'rejected',
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return JSONResponse(content={
                'success': True,
                'message': 'Job request rejected'
            })
        else:
            return JSONResponse(content={
                'success': False,
                'message': 'Request not found or already processed'
            }, status_code=404)
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'message': f'Failed to reject request: {str(e)}'
        }, status_code=500)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  🌐 Starting Web Interface for AI Freelancer Evaluation System")
    print("=" * 70)
    print("\n📍 Web Interface: http://localhost:3000")
    print("📍 API Backend: http://localhost:8000 (must be running)")
    print("\n🔐 Authentication: MongoDB-based with email validation")
    print("   - Signup required before login")
    print("   - Passwords are securely hashed")
    print("   - Email must be unique")
    print("\n⏸️  Press Ctrl+C to stop the server\n")
    
    uvicorn.run(web_app, host="0.0.0.0", port=3000, log_level="info")
