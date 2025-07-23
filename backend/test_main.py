from fastapi import FastAPI

app = FastAPI(title="로봇 행동 태깅 API 테스트")


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
