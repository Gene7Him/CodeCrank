from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from pydantic import BaseModel
from . import docker_runner
import tempfile
import os
import shutil
import git
import subprocess


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RepoRequest(BaseModel):
    repo_url: str

@app.post("/run-repo/")
def run_repo(request: RepoRequest):
    #return docker_runner.run_in_docker(request.repo_url)
    repo_url = request.repo_url.rstrip('/')

    temp_dir = tempfile.mkdtemp()

    try:
        git.Repo.clone_from(repo_url, temp_dir)
        main_file = find_entrypoint(temp_dir)

        if not main_file:
            return {"error": "No runnable file found."}

        result = subprocess.run(
            ["python3", main_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=temp_dir
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        shutil.rmtree(temp_dir)

def find_entrypoint(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().startswith("main") and file.endswith(".py"):
                return os.path.join(root, file)
    return None
