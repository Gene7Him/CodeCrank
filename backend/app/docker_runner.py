import docker
import tempfile
import os
import shutil
import git
import uuid
import re

client = docker.from_env()

def clone_repo(repo_url):
    temp_dir = tempfile.mkdtemp()
    git.Repo.clone_from(repo_url, temp_dir)
    return temp_dir

def detect_language(repo_path):
    for file in os.listdir(repo_path):
        if file.endswith(".py"):
            return "python"
        elif file.endswith(".js"):
            return "node"
        elif file.endswith(".java"):
            return "java"
    return "unknown"

def find_entrypoint(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().startswith("main") and file.endswith(".py"):
                return os.path.join(root, file)
            if file.lower().startswith("app") and file.endswith(".py"):
                return os.path.join(root, file)
            if file.lower().startswith("index") and file.endswith(".py"):
                return os.path.join(root, file)
            if file.lower().startswith("main") and file.endswith(".js"):
                return os.path.join(root, file)
            if file.lower().startswith("main") and file.endswith(".java"):
                return os.path.join(root, file)
    return None

def run_in_docker(repo_url):
    temp_dir = clone_repo(repo_url)
    language = detect_language(temp_dir)

    try:
        entry_file = find_entrypoint(temp_dir)
        if not entry_file:
            return {"error": "No entry file found in repo."}
        rel_entry = os.path.relpath(entry_file, temp_dir)

        if language == "python":
            dockerfile = f"""
            FROM python:3.10-slim
            WORKDIR /app
            COPY . .

            RUN apt-get update && apt-get install -y gcc g++ git curl && apt-get clean

            RUN pip install --no-cache-dir \\
                numpy pandas matplotlib seaborn \\
                scikit-learn tensorflow torch \\
                transformers requests aiohttp \\
                fastapi starlette jinja2 aiofiles uvicorn \\
                sqlalchemy psycopg2-binary opencv-python \\
                flask django \\
                pillow nltk spacy tqdm

            CMD ["python3", "{rel_entry}"]
            """

        elif language == "node":
            dockerfile = f"""
            FROM node:18-alpine
            WORKDIR /app
            COPY . .
            RUN npm install || true
            CMD ["node", "{rel_entry}"]
            """

        elif language == "java":
            dockerfile = f"""
            FROM openjdk:17
            WORKDIR /app
            COPY . .
            RUN javac {rel_entry}
            CMD ["java", "{rel_entry.replace('.java', '')}"]
            """

        else:
            return {"error": "Unsupported language."}

        with open(os.path.join(temp_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile.strip())

        tag = f"codecrank-{uuid.uuid4()}"
        image = client.images.build(path=temp_dir, tag=tag, rm=True, pull=True)[0]
        logs = client.containers.run(image.id, remove=True)
        return {"stdout": logs.decode("utf-8"), "language": language}

    except Exception as e:
        return {"error": str(e)}

    finally:
        shutil.rmtree(temp_dir)
