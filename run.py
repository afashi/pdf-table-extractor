# /run.py

import eventlet
# 1. 在这里应用猴子补丁，这是我们能做到的最早的时刻。
eventlet.monkey_patch()

import uvicorn

if __name__ == "__main__":
    # 2. 以编程方式启动 Uvicorn
    #    我们直接告诉它去哪里找 FastAPI 的 app 实例。
    uvicorn.run(
        "src.pdf_extractor.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # 在开发时保持重载功能
        workers=1     # 在使用 eventlet 时，通常将 worker 数量设为 1
    )