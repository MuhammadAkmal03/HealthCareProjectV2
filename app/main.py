import logging
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.api import symptom_predictor, scan_analyzer, health_assistant

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Healthcare AI API",
    description="API for all healthcare modules.",
    version="1.0.0",
    redirect_slashes=False
)

origins = [
    "https://health-care-project-v2.vercel.app",
    "https://healthpro2-api-qlbrqss62q-uc.a.run.app",
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "null"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(
    symptom_predictor.router, prefix="/predict", tags=["Symptom Predictor"]
)
app.include_router(scan_analyzer.router, prefix="/analyze", tags=["Scan Analyzer"])
app.include_router(health_assistant.router, prefix="/assistant", tags=["AI Assistant"])


def _prewarm_services():
    """Pre-loads heavy ML models using the same singletons the API uses."""
    try:
        logger.info("Pre-warming ImageService (TF model)...")
        from app.api.scan_analyzer import get_image_service
        get_image_service()
        logger.info("ImageService pre-warm complete.")
    except Exception as e:
        logger.warning(f"ImageService pre-warm failed (non-fatal): {e}")

    try:
        logger.info("Pre-warming ChatbotService (HuggingFace embeddings)...")
        from app.api.health_assistant import get_chatbot_service
        get_chatbot_service()
        logger.info("ChatbotService pre-warm complete.")
    except Exception as e:
        logger.warning(f"ChatbotService pre-warm failed (non-fatal): {e}")


@app.on_event("startup")
async def startup_event():
    """Starts background pre-warming after server is ready to accept requests."""
    thread = threading.Thread(target=_prewarm_services, daemon=True)
    thread.start()
    logger.info("Background pre-warming thread started.")


@app.get("/", tags=["Health Check"])
def read_root():
    logger.info("Health check endpoint was called.")
    return {"status": "ok", "message": "Welcome to the Healthcare AI API!"}