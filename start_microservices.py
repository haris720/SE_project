"""
Microservices Startup Script
Starts all microservices in separate processes
"""

import subprocess
import time
import sys
import os

def start_microservices():
    """Start all microservices"""
    print("\n" + "=" * 70)
    print("🚀 STARTING MICROSERVICES ARCHITECTURE")
    print("=" * 70)
    print("\n📦 Services will start in the following order:")
    print("   1. Trust Score AI Service (port 8001)")
    print("   2. Cost & Time Estimation Service (port 8002)")
    print("   3. API Gateway / Web Interface (port 3000)")
    print("\n⏳ Please wait for all services to initialize...\n")
    
    # Determine Python command
    python_cmd = "py -3.11" if sys.platform == "win32" else "python3.11"
    
    processes = []
    
    try:
        # Start Trust Score Service
        print("🔵 Starting Trust Score AI Service...")
        trust_score_process = subprocess.Popen(
            f"{python_cmd} trust_score_service.py",
            shell=True,
            cwd=os.getcwd()
        )
        processes.append(("Trust Score Service", trust_score_process))
        time.sleep(3)  # Give it time to start
        
        # Start Cost/Time Service
        print("🟢 Starting Cost & Time Estimation Service...")
        cost_time_process = subprocess.Popen(
            f"{python_cmd} cost_time_service_api.py",
            shell=True,
            cwd=os.getcwd()
        )
        processes.append(("Cost/Time Service", cost_time_process))
        time.sleep(3)  # Give it time to start
        
        # Start Web Gateway
        print("🟡 Starting API Gateway / Web Interface...")
        web_process = subprocess.Popen(
            f"{python_cmd} web_app.py",
            shell=True,
            cwd=os.getcwd()
        )
        processes.append(("Web Gateway", web_process))
        time.sleep(3)
        
        print("\n" + "=" * 70)
        print("✅ ALL MICROSERVICES STARTED SUCCESSFULLY")
        print("=" * 70)
        print("\n📍 Service URLs:")
        print("   • Trust Score Service: http://localhost:8001")
        print("   • Cost/Time Service: http://localhost:8002")
        print("   • Web Application: http://localhost:3000")
        print("\n📚 API Documentation:")
        print("   • Trust Score API Docs: http://localhost:8001/docs")
        print("   • Cost/Time API Docs: http://localhost:8002/docs")
        print("\n🏗️  Architecture: Microservices")
        print("   • Each service runs independently")
        print("   • Services communicate via HTTP REST APIs")
        print("   • Gateway orchestrates requests to AI services")
        print("\n⏸️  Press Ctrl+C to stop all services\n")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\n⚠️  {name} has stopped unexpectedly!")
                    raise KeyboardInterrupt
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("🛑 SHUTTING DOWN ALL MICROSERVICES")
        print("=" * 70)
        
        # Terminate all processes
        for name, proc in processes:
            try:
                print(f"   Stopping {name}...")
                proc.terminate()
                proc.wait(timeout=5)
            except Exception as e:
                print(f"   Force killing {name}...")
                proc.kill()
        
        print("\n✅ All services stopped successfully")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    start_microservices()
