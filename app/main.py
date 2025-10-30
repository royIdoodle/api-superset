from fastapi import FastAPI

from .database import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(title="OSS 图片资源管理 API", version="0.1.0")

    # 路由
    from .routers import images, stats, test  # 延迟导入以避免循环

    app.include_router(images.router, prefix="/images", tags=["images"])
    app.include_router(stats.router, prefix="/stats", tags=["stats"])
    app.include_router(test.router, prefix="/test", tags=["test"]) 

    @app.on_event("startup")
    def on_startup() -> None:
        # 初始化数据库表
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()


