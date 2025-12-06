# Freelancer AI Platform

A comprehensive freelancer marketplace platform with AI-powered features including trust score prediction, cost estimation, and time prediction for projects.

##  Features

- **AI Trust Score**: Machine learning-based trust score prediction for freelancers using Random Forest algorithm
- **AI Cost Estimation**: LightGBM-based cost prediction using TF-IDF text analysis and project complexity
- **Time Prediction**: Automated delivery time estimation based on project requirements
- **User Management**: Separate dashboards for freelancers and clients
- **Job Posting & Management**: Complete job lifecycle from posting to completion
- **Real-time Validation**: Smart description validation with technical keyword recognition

##  Prerequisites

- **Python 3.11** (Required - This project is built and tested with Python 3.11)
- MongoDB (local installation or MongoDB Atlas cloud)
- Git (for cloning the repository)

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd SE-project
```

### Step 2: Verify Python Version

Ensure you have Python 3.11 installed:

```bash
python --version
# or
py -3.11 --version
```

If you don't have Python 3.11, download it from [python.org](https://www.python.org/downloads/)

### Step 3: Create Virtual Environment (Recommended)

```bash
# Windows
py -3.11 -m venv venv
venv\Scripts\activate

# Linux/Mac
python3.11 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages include:
- FastAPI (web framework)
- uvicorn (ASGI server)
- pymongo (MongoDB driver)
- scikit-learn (machine learning)
- lightgbm (gradient boosting)
- xgboost (alternative ML model)
- pandas, numpy (data processing)
- Jinja2 (templating)

### Step 5: Configure MongoDB

1. **Option A: Local MongoDB**
   - Install MongoDB Community Edition from [mongodb.com](https://www.mongodb.com/try/download/community)
   - Start MongoDB service:
     ```bash
     # Windows
     net start MongoDB
     
     # Linux
     sudo systemctl start mongod
     
     # Mac
     brew services start mongodb-community
     ```

2. **Option B: MongoDB Atlas (Cloud)**
   - Create a free account at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Create a cluster and get your connection string
   - Update `config.py` with your connection string

### Step 6: Configure Application Settings

Edit `config.py` to match your setup:

```python
# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"  # or your MongoDB Atlas URI
DATABASE_NAME = "freelancer_ai_db"

# Application Settings
SECRET_KEY = "your-secret-key-here"
```

### Step 7: Train AI Models (First Time Only)

Before running the application for the first time, train the AI models:

```bash
py -3.11 -c "from services.cost_time_service import train_cost_time_models; train_cost_time_models(use_lightgbm=True)"
```

This will:
- Generate 800 training samples
- Train cost estimation model (R² ≈ 0.95)
- Train time prediction model (R² ≈ 0.93)
- Save models to `models/` directory

### Step 8: Run the Application

```bash
py -3.11 web_app.py
```

The application will start on **http://localhost:3000**

##  Accessing the Application

1. Open your web browser
2. Navigate to: **http://localhost:3000**
3. You'll see the home page with login/signup options

##  Project Structure

```
SE-project/
├── web_app.py              # Main FastAPI application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── database/              # MongoDB models
│   ├── user.py           # User model
│   ├── job.py            # Job model
│   └── request.py        # Request model
├── services/             # Business logic
│   ├── cost_time_service.py    # AI cost/time prediction
│   ├── trust_score_ai.py       # AI trust score
│   └── models/                 # Trained ML models
├── web/                  # Frontend
│   ├── templates/        # HTML templates
│   ├── static/          # CSS, JS, images
│   └── auth.py          # Authentication
└── models/              # Saved AI models (.pkl files)
```

##  AI Models Specifications

### 1. Cost Estimation Model
- **Algorithm**: LightGBM Regressor
- **Features**: TF-IDF (500 features), complexity multiplier, skills count, description metrics
- **Performance**: R² = 0.95, MAE = 19.12
- **Scaling**: Manual description multiplier (1.0x - 3.5x) based on:
  - Word count (longer = higher cost)
  - Technical keyword density
  - Sentence complexity

### 2. Time Prediction Model
- **Algorithm**: LightGBM Regressor
- **Features**: Same as cost model
- **Performance**: R² = 0.93, MAE = 0.37 days
- **Range**: 1-30 days typical delivery time

### 3. Trust Score Model
- **Algorithm**: Random Forest Classifier
- **Features**: Jobs completed, success rate, ratings, response time, earnings, projects
- **Performance**: R² = 0.9904
- **Categories**: Elite (90-100), Good (70-89), Developing (50-69), Struggling (0-49)

##  Default Test Accounts

For testing purposes, you can create accounts through the signup page:

**Freelancer Account:**
- Register as "Freelancer" during signup
- Access trust score prediction
- View and apply to available jobs

**Client Account:**
- Register as "Client" during signup
- Post jobs with AI cost estimation
- View freelancer applications
- Manage job assignments

##  Usage Flow

### For Clients:
1. Sign up / Log in as Client
2. Navigate to "Post Job" section
3. Enter job details (description, skills, complexity)
4. Get AI-powered cost and time estimates
5. Post the job
6. Review freelancer applications
7. Assign job to selected freelancer
8. Mark job as completed when done

### For Freelancers:
1. Sign up / Log in as Freelancer
2. Complete profile with skills
3. View AI-predicted trust score
4. Browse available jobs
5. Apply to jobs matching skills
6. Work on assigned jobs
7. Submit completed work

##  Troubleshooting

### MongoDB Connection Issues
```
Error: Failed to connect to MongoDB
```
**Solution**: 
- Verify MongoDB is running: `mongosh` or check MongoDB Compass
- Check connection string in `config.py`
- Ensure firewall allows MongoDB port (27017)

### Python Version Issues
```
Error: Python 3.11 required
```
**Solution**:
- Use `py -3.11` command explicitly
- Or activate virtual environment with Python 3.11

### Missing Dependencies
```
Error: ModuleNotFoundError
```
**Solution**:
```bash
pip install -r requirements.txt
```

### AI Model Not Found
```
Error: Model file not found
```
**Solution**:
- Run model training command from Step 7
- Check `models/` directory contains .pkl files

### Port Already in Use
```
Error: Address already in use
```
**Solution**:
```bash
# Windows - Find and kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

##  Updating the Application

To update to the latest version:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
py -3.11 web_app.py
```

##  Testing

The application includes validation for:
- Description quality (technical keyword recognition)
- Email format validation
- Password strength requirements
- Skills input validation

##  Technical Details

### Validation Rules:
- **Description**: Minimum 10 characters, 3 words, 15%-75% vowel ratio
- **Technical Keywords**: 200+ recognized terms (Python, AWS, Docker, React, etc.)
- **Consonant Clusters**: Maximum 6 consecutive consonants allowed
- **Cost Range**: Dynamic ±15% to ±25% based on project complexity

### API Endpoints:
- `POST /api/signup` - User registration
- `POST /api/login` - User authentication
- `GET /api/jobs` - List all jobs
- `POST /api/jobs` - Create new job
- `POST /api/jobs/estimate` - Get AI cost/time estimate
- `GET /api/trust-score` - Get freelancer trust score



##  Version Information

- **Python**: 3.11 (Required)
- **Framework**: FastAPI
- **Database**: MongoDB
- **ML Libraries**: scikit-learn, LightGBM, XGBoost
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

---

**Note**: Always use Python 3.11 for this project. Other Python versions may cause compatibility issues with dependencies and AI models.
