import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def run_command(command):
    """Run a command and return its output"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}:")
        print(e.stderr)
        return None

def main():
    # Get the project directory
    project_dir = Path(__file__).parent / 'voting_system'
    
    if not project_dir.exists():
        print(f"Error: Project directory not found at {project_dir}")
        return
    
    # Change to the project directory
    os.chdir(project_dir)
    
    # Add the project directory to Python path
    sys.path.append(str(project_dir))
    
    print("Starting University Voting System...")
    print("\n1. Checking for migrations...")
    
    # Check for migrations
    migrations_output = run_command([sys.executable, 'manage.py', 'makemigrations'])
    if migrations_output is None:
        return
    
    if "No changes detected" not in migrations_output:
        print("New migrations detected.")
    
    print("\n2. Applying migrations...")
    if run_command([sys.executable, 'manage.py', 'migrate']) is None:
        return
    
    print("\n3. Starting development server...")
    
    # Start the server
    server_process = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a bit for the server to start
    time.sleep(2)
    
    # Check if the server started successfully
    if server_process.poll() is not None:
        print("Error: Server failed to start")
        print(server_process.stderr.read())
        return
    
    print("\nServer is running!")
    print("\nAccess the application at:")
    print("Main site: http://127.0.0.1:8000")
    print("Admin interface: http://127.0.0.1:8000/admin")
    
    # Open the browser
    try:
        webbrowser.open('http://127.0.0.1:8000')
    except:
        print("Note: Could not open browser automatically.")
    
    print("\nPress Ctrl+C to stop the server.")
    
    try:
        # Keep the script running and display server output
        while True:
            line = server_process.stdout.readline()
            if line:
                print(line.rstrip())
            if server_process.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped.")

if __name__ == '__main__':
    main()
