import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.database import Base, engine, wait_for_db
from app.routers import tasks

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("microservice")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при запуске (startup)
    logger.info("Initializing microservice and checking DB connection...")
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
    yield
    # Действия при остановке (shutdown)
    logger.info("Shutting down microservice...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Микросервис управления задачами (REST API, PostgreSQL, Docker, Swagger UI)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Middleware для логирования всех запросов и времени выполнения
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Incoming request: {method} {path} from {client_ip}")

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Completed: {method} {path} with status {response.status_code} in {process_time:.2f}ms")
        return response
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Failed: {method} {path} error: {exc} after {process_time:.2f}ms", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "message": "Внутренняя ошибка сервера", "detail": str(exc)}
        )

# Обработчик ошибок валидации входных данных (Pydantic / 422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    formatted_errors = [{"field": " -> ".join(str(loc) for loc in err["loc"]), "msg": err["msg"]} for err in errors]
    logger.warning(f"Validation failed on {request.method} {request.url.path}: {formatted_errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Переданы некорректные данные в запросе",
            "details": formatted_errors
        }
    )

# Обработчик HTTP исключений (404, 400 и др.)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException on {request.method} {request.url.path}: code={exc.status_code}, detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "ClientError",
            "message": exc.detail
        }
    )

# Корневой маршрут и Healthcheck
@app.get("/", tags=["Health"])
def healthcheck():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "docs": "/docs"
    }

# Подключение роутера задач
app.include_router(tasks.router, prefix=settings.API_V1_STR, tags=["Tasks"])
