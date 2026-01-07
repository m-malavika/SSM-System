"""Start the backend server"""
import os
import sys

if __name__ == "__main__":
    # Change to backend directory
    backend_dir = r"C:\Users\renis\OneDrive\Desktop\malu\SSM-System\backend"
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)

    # Start uvicorn
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
