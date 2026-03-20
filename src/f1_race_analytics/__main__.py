import uvicorn


def start():
    uvicorn.run("f1_race_analytics.app:app", reload=True)


def live():
    uvicorn.run(
        "f1_race_analytics.live_api:app",
        reload=True,
        port=8001,
    )
