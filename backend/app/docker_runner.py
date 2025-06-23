import docker
import tempfile
import os
import shutil
import git
import uuid

client = docker.from_env()

def clone_repo(repo_url):
    temp_dir = tempfile.mkdtemp()
    git.Repo.clone_from(repo_url, temp_dir)
    return temp_dir

def detect_language(repo_path):
    files = os.listdir(repo_path)
    if any(f.endswith(".py") for f in files):
        return "python"
    elif any(f.endswith(".js") for f in files):
        return "node"
    elif any(f.endswith(".java") for f in files):
        return "java"
    return "unknown"

def run_in_docker(repo_url):
    temp_dir = clone_repo(repo_url)
    language = detect_language(temp_dir)
    container = None

    try:
        if language == "python":
            dockerfile = f"""
            FROM python:3.10-slim
            WORKDIR /app
            COPY . .
            CMD ["python3", "main.py"]
            """
        elif language == "node":
            dockerfile = f"""
            FROM node:18-alpine
            WORKDIR /app
            COPY . .
            RUN npm install || true
            CMD ["node", "index.js"]
            """
        elif language == "java":
            dockerfile = f"""
            FROM openjdk:17
            WORKDIR /app
            COPY . .
            RUN javac Main.java
            CMD ["java", "Main"]
            """
        else:
            return {"error": "Unsupported language."}

        with open(os.path.join(temp_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile)

        tag = f"replrunner-{uuid.uuid4()}"
        image = client.images.build(path=temp_dir, tag=tag)[0]
        logs = client.containers.run(image.id, remove=True)
        return {"stdout": logs.decode("utf-8"), "language": language}

    except Exception as e:
        return {"error": str(e)}

    finally:
        shutil.rmtree(temp_dir)
