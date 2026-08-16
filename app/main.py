from fastapi import FastAPI

app = FastAPI(title="LUMINA Wearables", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "lumina-wearables"}
