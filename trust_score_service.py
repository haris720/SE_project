"""
Trust Score Microservice - Independent AI Service
Runs on port 8001 and provides trust score predictions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.trust_score_ai import TrustScoreAI

# Initialize AI service
trust_score_ai = TrustScoreAI()

# Load model on startup - using lifespan context manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load AI model on service startup"""
    try:
        trust_score_ai.load_model()
        print("✅ Trust Score AI model loaded successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not load AI model: {e}")
        print("   Training model now...")
        try:
            trust_score_ai.train_model(n_samples=2000)
            print("✅ Trust Score AI model trained successfully")
        except Exception as train_error:
            print(f"❌ Error training model: {train_error}")
    yield
    # Cleanup on shutdown
    print("Shutting down Trust Score Service...")

# Create FastAPI app with lifespan
app = FastAPI(title="Trust Score AI Microservice", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class TrustScoreRequest(BaseModel):
    user_id: str


class HealthResponse(BaseModel):
    status: str
    service: str
    model_loaded: bool


class TrustScoreResponse(BaseModel):
    user_id: str
    trust_score: float
    interpretation: str
    confidence: float
    rating: float
    success_rate: float
    sentiment_score: float
    skills_count: int
    completed_jobs: int
    calculation: str
    success: bool
    message: Optional[str] = None


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Trust Score AI Microservice",
        "model_loaded": trust_score_ai.model is not None
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "Trust Score AI Microservice",
        "model_loaded": trust_score_ai.model is not None
    }


@app.post("/api/predict", response_model=TrustScoreResponse)
async def predict_trust_score(request: TrustScoreRequest):
    """
    Predict trust score for a freelancer
    
    Args:
        request: Contains user_id of the freelancer
        
    Returns:
        Trust score prediction (0-100)
    """
    try:
        if trust_score_ai.model is None:
            raise HTTPException(
                status_code=503,
                detail="AI model not loaded. Service unavailable."
            )
        
        # Get trust score from AI model (returns dict with all metrics)
        result = trust_score_ai.predict_trust_score(request.user_id)
        
        return {
            "user_id": request.user_id,
            "trust_score": result['trust_score'],
            "interpretation": result.get('interpretation', ''),
            "confidence": result.get('confidence', 0),
            "rating": result.get('rating', 0),
            "success_rate": result.get('success_rate', 0),
            "sentiment_score": result.get('sentiment_score', 0),
            "skills_count": result.get('skills_count', 0),
            "completed_jobs": result.get('completed_jobs', 0),
            "calculation": result.get('calculation', 'AI Model'),
            "success": True,
            "message": "Trust score predicted successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error predicting trust score: {str(e)}"
        )


@app.post("/api/train")
async def train_model(n_samples: int = 2000):
    """
    Train/retrain the AI model
    
    Args:
        n_samples: Number of training samples to generate
        
    Returns:
        Training results and metrics
    """
    try:
        results = trust_score_ai.train_model(n_samples=n_samples)
        return {
            "success": True,
            "message": "Model trained successfully",
            "metrics": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error training model: {str(e)}"
        )


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 TRUST SCORE AI MICROSERVICE")
    print("=" * 70)
    print("\n📍 Service URL: http://localhost:8001")
    print("📍 API Documentation: http://localhost:8001/docs")
    print("\n🤖 AI Model: Random Forest Regressor")
    print("📊 Features: Rating, Success Rate, Sentiment, Jobs, Skills, Earnings")
    print("\n⏸️  Press Ctrl+C to stop the service\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
