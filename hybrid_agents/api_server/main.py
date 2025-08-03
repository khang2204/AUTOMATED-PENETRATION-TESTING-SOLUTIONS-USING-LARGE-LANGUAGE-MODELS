from fastapi import FastAPI
from api_server.agent_router import agent_router

app = FastAPI()
app.include_router(agent_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server.main:app", host="0.0.0.0", port=8000, reload=False)