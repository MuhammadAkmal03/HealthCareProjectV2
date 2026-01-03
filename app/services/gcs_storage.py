"""
Google Cloud Storage backup/restore for SQLite database.
Ensures analytics data persists across Cloud Run container restarts.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Configuration
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
DB_PATH = "predictions.db"
GCS_DB_PATH = "analytics/predictions.db"

# Only import GCS if bucket is configured
_gcs_available = False
_client = None
_bucket = None

if GCS_BUCKET_NAME:
    try:
        from google.cloud import storage
        _client = storage.Client()
        _bucket = _client.bucket(GCS_BUCKET_NAME)
        _gcs_available = True
        logger.info(f"GCS storage initialized with bucket: {GCS_BUCKET_NAME}")
    except Exception as e:
        logger.warning(f"GCS not available: {e}. Data will not persist across restarts.")


def restore_db_from_gcs():
    """Download database from GCS on startup if it exists."""
    if not _gcs_available:
        logger.info("GCS not configured, skipping restore.")
        return False
    
    try:
        blob = _bucket.blob(GCS_DB_PATH)
        if blob.exists():
            blob.download_to_filename(DB_PATH)
            logger.info(f"✓ Restored database from GCS: {GCS_DB_PATH}")
            return True
        else:
            logger.info("No existing database in GCS (first run).")
            return False
    except Exception as e:
        logger.error(f"Failed to restore from GCS: {e}")
        return False


def backup_db_to_gcs():
    """Upload database to GCS after write operations."""
    if not _gcs_available:
        return False
    
    if not os.path.exists(DB_PATH):
        logger.warning(f"Database file not found: {DB_PATH}")
        return False
    
    try:
        blob = _bucket.blob(GCS_DB_PATH)
        blob.upload_from_filename(DB_PATH)
        logger.info(f"✓ Backed up database to GCS: {GCS_DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to backup to GCS: {e}")
        return False


def is_gcs_available():
    """Check if GCS is configured and available."""
    return _gcs_available
