# Microservices Architecture - Quick Start Guide

## 🏗️ Architecture Overview

Your project now follows a **true Microservices Architecture** with three independent services:

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (Port 3000)                 │
│                  (web_app.py - FastAPI)                     │
│         Routes HTTP requests to appropriate services        │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             │ HTTP REST                  │ HTTP REST
             │                            │
    ┌────────▼────────┐          ┌────────▼────────┐
    │  Trust Score    │          │  Cost & Time    │
    │  AI Service     │          │  Estimation     │
    │  (Port 8001)    │          │  Service        │
    │                 │          │  (Port 8002)    │
    │ Random Forest   │          │  LightGBM       │
    └─────────────────┘          └─────────────────┘
```

## 📦 Microservices

### 1. **Trust Score AI Service** (Port 8001)
- **File**: `trust_score_service.py`
- **Technology**: Random Forest Regressor
- **Purpose**: Predicts freelancer trustworthiness (0-100)
- **Features**: Rating, success rate, sentiment, jobs completed
- **API Docs**: http://localhost:8001/docs

### 2. **Cost & Time Estimation Service** (Port 8002)
- **File**: `cost_time_service_api.py`
- **Technology**: LightGBM + TF-IDF
- **Purpose**: Predicts project cost and delivery time
- **Features**: Description analysis, skills, complexity
- **API Docs**: http://localhost:8002/docs

### 3. **API Gateway / Web Interface** (Port 3000)
- **File**: `web_app.py`
- **Purpose**: User interface and request orchestration
- **Routes**: Forwards requests to microservices via HTTP
- **Web App**: http://localhost:3000

## 🚀 How to Run

### Option 1: Automatic (Recommended)
Simply double-click or run:
```bash
start_all.bat
```
This starts all three services automatically.

### Option 2: Manual Start (Individual Services)
Open **3 separate terminals** and run:

**Terminal 1 - Trust Score Service:**
```bash
py -3.11 trust_score_service.py
```

**Terminal 2 - Cost/Time Service:**
```bash
py -3.11 cost_time_service_api.py
```

**Terminal 3 - Web Gateway:**
```bash
py -3.11 web_app.py
```

### Option 3: Python Script
```bash
py -3.11 start_microservices.py
```

## ✅ Benefits of This Architecture

### 1. **Independent Deployment**
- Each service can be deployed separately
- Update one service without affecting others
- Different release cycles for each service

### 2. **Independent Scaling**
- Scale Trust Score service if heavy traffic on freelancer profiles
- Scale Cost/Time service independently during project creation peaks
- Horizontal scaling per service needs

### 3. **Technology Flexibility**
- Trust Score uses Random Forest
- Cost/Time uses LightGBM
- Can change one without affecting the other

### 4. **Fault Isolation**
- If Trust Score service crashes, Cost/Time still works
- Gateway has fallback mechanisms
- Better resilience

### 5. **Service-to-Service Communication**
- HTTP REST APIs (standard microservices pattern)
- Can add service discovery later
- Can add API gateway features (rate limiting, auth)

## 🔍 Service Communication Flow

### Example: Get Trust Score
```
User Request → Gateway (3000) 
            → HTTP POST to Trust Score Service (8001) 
            → ML Prediction 
            → Response to Gateway 
            → Response to User
```

### Example: Job Cost Estimation
```
User Request → Gateway (3000) 
            → HTTP POST to Cost/Time Service (8002) 
            → TF-IDF + LightGBM Prediction 
            → Response to Gateway 
            → Response to User
```

## 📊 Architecture Compliance

✅ **Separation of Responsibilities**: Each service has its own logic  
✅ **Independent Updates**: Can update one without touching others  
✅ **Better Scalability**: Each service scales independently  
✅ **Flexibility**: Different technologies per service  
✅ **Fault Isolation**: Service failures are isolated  
✅ **HTTP Communication**: Services talk via REST APIs  
✅ **Independent Deployment**: Each service is a separate process  

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Data Storage | MongoDB |
| Preprocessing | Pandas, NumPy |
| ML Models | Scikit-learn (RandomForest), LightGBM |
| NLP Processing | TF-IDF Vectorizer |
| API Layer | FastAPI (3 instances) |
| Service Communication | HTTP/REST (httpx) |
| Architecture | **Microservices** ✅ |

## 🔐 Requirements

Before running, ensure you have:
- Python 3.11
- MongoDB running (local or Atlas)
- All dependencies: `pip install -r requirements.txt`

## 📝 Notes

- Each service runs in its own process
- Services must all be running for full functionality
- Gateway checks service health on startup
- Services can be deployed to different servers/containers
- Add Docker support for containerization (future)
- Add Kubernetes for orchestration (future)

## 🎯 Next Steps for Production

1. **Containerization**: Add Dockerfile for each service
2. **Service Discovery**: Implement Consul or Eureka
3. **API Gateway**: Use Kong or AWS API Gateway
4. **Monitoring**: Add Prometheus + Grafana
5. **Logging**: Centralized logging (ELK stack)
6. **Load Balancing**: Nginx or cloud load balancers
7. **CI/CD**: Separate pipelines per service
