# HOW TO RUN MICROSERVICES - STEP BY STEP GUIDE

## ✅ Prerequisites Check

1. **Python 3.11 Installed**
   ```powershell
   py -3.11 --version
   ```
   Should show: Python 3.11.x

2. **MongoDB Running**
   - Make sure MongoDB is running on your machine
   - Check with: `mongod --version` or verify MongoDB service is running

3. **Install Required Packages**
   ```powershell
   py -3.11 -m pip install -r requirements.txt
   ```

## 🚀 OPTION 1: Automatic Start (RECOMMENDED)

### Step 1: Double-click this file
```
start_services.bat
```

This will:
- Open 3 separate command windows
- Each service runs in its own window
- Wait 15 seconds for all services to start

### Step 2: Verify Services are Running
- Window 1: Trust Score Service (Port 8001)
- Window 2: Cost/Time Service (Port 8002)  
- Window 3: Web Application (Port 3000)

### Step 3: Access the Application
Open browser: **http://localhost:3000**

---

## 🔧 OPTION 2: Manual Start (If automatic doesn't work)

### Step 1: Start Trust Score Service
Open **Command Prompt #1**:
```powershell
cd D:\SE-project
py -3.11 trust_score_service.py
```

**Wait for this message:**
```
✅ Trust Score AI model loaded successfully
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Step 2: Start Cost/Time Service  
Open **Command Prompt #2**:
```powershell
cd D:\SE-project
py -3.11 cost_time_service_api.py
```

**Wait for this message:**
```
✅ Cost & Time estimation models loaded successfully
INFO:     Uvicorn running on http://0.0.0.0:8002
```

### Step 3: Start Web Application
Open **Command Prompt #3**:
```powershell
cd D:\SE-project
py -3.11 web_app.py
```

**Wait for this message:**
```
✅ Trust Score Service: Online (port 8001)
✅ Cost/Time Estimation Service: Online (port 8002)
INFO:     Uvicorn running on http://0.0.0.0:3000
```

### Step 4: Access the Application
Open browser: **http://localhost:3000**

---

## 🔍 TROUBLESHOOTING

### Error: "Cost/Time estimation service error"

**Cause:** Web app started before microservices were ready

**Solution:**
1. Stop all services (close command windows or press Ctrl+C)
2. Start services IN ORDER (Trust Score → Cost/Time → Web App)
3. Wait 5 seconds between each service

### Error: "ModuleNotFoundError: No module named 'httpx'"

**Solution:**
```powershell
py -3.11 -m pip install httpx
```

### Error: Port already in use

**Solution:**
```powershell
# Kill all Python processes
Stop-Process -Name python -Force
# Then restart services
```

### Error: MongoDB connection failed

**Solution:**
1. Start MongoDB service
2. Or check `config.py` for correct MongoDB connection string

---

## 📊 Service Health Check

### Check if services are running:

**Trust Score Service:**
```powershell
curl http://localhost:8001/health
```
Should return: `{"status":"healthy","service":"Trust Score AI Microservice","model_loaded":true}`

**Cost/Time Service:**
```powershell
curl http://localhost:8002/health
```
Should return: `{"status":"healthy","service":"Cost & Time Estimation Microservice","models_loaded":true}`

**Web Application:**
```powershell
curl http://localhost:3000/
```
Should return HTML content

---

## 🛑 How to Stop All Services

### Option 1: Close Windows
Just close the 3 command prompt windows

### Option 2: PowerShell Command
```powershell
Stop-Process -Name python -Force
```

---

## 📝 Service URLs

| Service | URL | API Docs |
|---------|-----|----------|
| Trust Score AI | http://localhost:8001 | http://localhost:8001/docs |
| Cost/Time Estimation | http://localhost:8002 | http://localhost:8002/docs |
| Web Application | http://localhost:3000 | (UI only) |

---

## ⚡ Quick Commands Reference

```powershell
# Install dependencies
py -3.11 -m pip install -r requirements.txt

# Start all services (automatic)
.\start_services.bat

# Check if services are running
Get-Process | Where-Object {$_.ProcessName -like '*python*'}

# Stop all services
Stop-Process -Name python -Force

# Test Trust Score service
curl http://localhost:8001/health

# Test Cost/Time service  
curl http://localhost:8002/health

# Access web app
start http://localhost:3000
```

---

## ✅ Success Indicators

When everything is working correctly:

1. **Three command windows are open** showing:
   - Trust Score Service logs
   - Cost/Time Service logs
   - Web Application logs

2. **No error messages** in any window

3. **Web app shows**:
   ```
   ✅ Trust Score Service: Online (port 8001)
   ✅ Cost/Time Estimation Service: Online (port 8002)
   ```

4. **Browser loads** http://localhost:3000 successfully

5. **"Get AI Estimation" button works** without errors

---

## 🎯 Common Startup Sequence

```
1. MongoDB Running ✓
2. Install Dependencies ✓
3. Start Trust Score Service (wait 5s) ✓
4. Start Cost/Time Service (wait 5s) ✓
5. Start Web Application (wait 5s) ✓
6. Open Browser → localhost:3000 ✓
7. Test "Get AI Estimation" ✓
```

**Total startup time: ~15-20 seconds**
