from fastapi import FastAPI

app = FastAPI(
    title="Secure API",
    description="A containerized API for learning DevSecOps practices.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}