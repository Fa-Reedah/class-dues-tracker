from fastapi import FastAPI

app = FastAPI(title="Class Dues Tracker", version="0.1.0")


@app.get("/")
def root():
    return {"status": "ok", "service": "class-dues-tracker"}


@app.get("/health")
def health():
    return {"healthy": True}
