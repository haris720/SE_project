"""
Cost & Time Estimation Microservice - Independent AI Service
Runs on port 8002 and provides project cost and time predictions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cost_time_service import CostTimeEstimationService

# Create FastAPI app for Cost/Time Estimation Service
# Will be redefined with lifespan below
app_temp = FastAPI(title="Cost & Time Estimation Microservice", version="1.0.0")

# Add CORS middleware
app_temp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI service
cost_service = CostTimeEstimationService()

# Load models on startup - using lifespan context manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load AI models on service startup"""
    try:
        cost_service.load_models()
        print("✅ Cost & Time estimation models loaded successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not load AI models: {e}")
        print("   Models will be trained on first prediction request")
    yield
    # Cleanup on shutdown
    print("Shutting down Cost & Time Estimation Service...")

# Create final app with lifespan
app = FastAPI(title="Cost & Time Estimation Microservice", version="1.0.0", lifespan=lifespan)

# Add CORS middleware to final app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class EstimationRequest(BaseModel):
    description: str
    skills_required: List[str]
    complexity: str


class ValidationRequest(BaseModel):
    description: str


class HealthResponse(BaseModel):
    status: str
    service: str
    models_loaded: bool


class ValidationResponse(BaseModel):
    valid: bool
    message: str


class EstimationResponse(BaseModel):
    estimated_cost_min: float
    estimated_cost_max: float
    estimated_days: int
    complexity: str
    valid: bool
    message: Optional[str] = None


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Cost & Time Estimation Microservice",
        "models_loaded": cost_service.cost_model is not None and cost_service.time_model is not None
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "Cost & Time Estimation Microservice",
        "models_loaded": cost_service.cost_model is not None and cost_service.time_model is not None
    }


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_description(request: ValidationRequest):
    """
    Validate project description
    
    Args:
        request: Contains project description
        
    Returns:
        Validation result with message
    """
    try:
        result = cost_service.validate_description(request.description)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating description: {str(e)}"
        )


@app.post("/api/estimate", response_model=EstimationResponse)
async def estimate_cost_time(request: EstimationRequest):
    """
    Estimate project cost and delivery time
    
    Args:
        request: Contains description, skills, and complexity
        
    Returns:
        Cost range and estimated days
    """
    try:
        # Validate description first
        validation = cost_service.validate_description(request.description)
        if not validation['valid']:
            return {
                "estimated_cost_min": 0,
                "estimated_cost_max": 0,
                "estimated_days": 0,
                "complexity": request.complexity,
                "valid": False,
                "message": validation['message']
            }
        
        # Check if models are loaded
        if cost_service.cost_model is None or cost_service.time_model is None:
            raise HTTPException(
                status_code=503,
                detail="AI models not loaded. Service unavailable."
            )
        
        # Get predictions
        project_data = {
            'description': request.description,
            'skills_required': request.skills_required,
            'complexity': request.complexity
        }
        result = cost_service.predict_cost_and_time(project_data)
        
        # Check if prediction returned an error
        if result.get('error'):
            return {
                "estimated_cost_min": 0,
                "estimated_cost_max": 0,
                "estimated_days": 0,
                "complexity": request.complexity,
                "valid": False,
                "message": result.get('message', 'Prediction failed')
            }
        
        return {
            "estimated_cost_min": result['min_cost'],
            "estimated_cost_max": result['max_cost'],
            "estimated_days": result['delivery_days'],
            "complexity": request.complexity,
            "valid": True,
            "message": "Estimation completed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error estimating project: {str(e)}"
        )


@app.post("/api/train")
async def train_models(n_samples: int = 5000):
    """
    Train/retrain the AI models
    
    Args:
        n_samples: Number of training samples to generate
        
    Returns:
        Training results and metrics
    """
    try:
        # Train models
        cost_service.train_models(n_samples=n_samples)
        
        return {
            "success": True,
            "message": "Models trained successfully",
            "n_samples": n_samples
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error training models: {str(e)}"
        )


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 COST & TIME ESTIMATION MICROSERVICE")
    print("=" * 70)
    print("\n📍 Service URL: http://localhost:8002")
    print("📍 API Documentation: http://localhost:8002/docs")
    print("\n🤖 AI Models: LightGBM/XGBoost with TF-IDF")
    print("📊 Features: Description Analysis, Skills, Complexity")
    print("\n⏸️  Press Ctrl+C to stop the service\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
