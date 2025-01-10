import uvicorn
import os

os.environ["START_INDEXING"] = "true"

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=True)