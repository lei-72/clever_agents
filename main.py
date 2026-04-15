"""本地与生产环境共用的 ASGI 入口。"""
import uvicorn

from app.main import app


if __name__ == "__main__":
    # 仅用于本地调试/测试时在 PyCharm 直接运行本文件启动服务。
    # 正式部署或统一启动脚本接入后，这段语句可以删除。
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info", reload=True)
