##############################################################################
"""
Enhanced main.py for Open WebUI
Author: Richard Scorpio (klyxmaster)
GitHub: https://github.com/klyxmaster/main4openwebui

Based on: Open WebUI - https://github.com/open-webui/open-webui
Original Author: Timothy Jaeryang Baek

Features:
- Persistent memory for likes, dislikes, people, and events
- Natural language trigger detection
- Time-aware responses and delayed session handling
- Dynamic system prompt injection (memory + context)

This version is maintained via GitHub. For the latest updates, improvements, or to contribute,
please visit the repository above.

Last updated: 2025-04-20
"""

##############################################################################
import asyncio
import inspect
import json
import logging
import mimetypes
import os
import shutil
import sys
import time
import random
from datetime import datetime
import pytz

from contextlib import asynccontextmanager
from urllib.parse import urlencode, parse_qs, urlparse
from pydantic import BaseModel
from sqlalchemy import text

from typing import Optional
from aiocache import cached
import aiohttp
import requests


from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
    applications,
    BackgroundTasks,
)

from fastapi.openapi.docs import get_swagger_ui_html

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response, StreamingResponse


from open_webui.utils import logger
from open_webui.utils.audit import AuditLevel, AuditLoggingMiddleware
from open_webui.utils.logger import start_logger
from open_webui.socket.main import (
    app as socket_app,
    periodic_usage_pool_cleanup,
)
from open_webui.routers import (
    audio,
    images,
    ollama,
    openai,
    retrieval,
    pipelines,
    tasks,
    auths,
    channels,
    chats,
    folders,
    configs,
    groups,
    files,
    functions,
    memories,
    models,
    knowledge,
    prompts,
    evaluations,
    tools,
    users,
    utils,
)

from open_webui.routers.retrieval import (
    get_embedding_function,
    get_ef,
    get_rf,
)

from open_webui.internal.db import Session, engine

from open_webui.models.functions import Functions
from open_webui.models.models import Models
from open_webui.models.users import UserModel, Users
from open_webui.models.chats import Chats

from open_webui.config import (
    LICENSE_KEY,
    # Ollama
    ENABLE_OLLAMA_API,
    OLLAMA_BASE_URLS,
    OLLAMA_API_CONFIGS,
    # OpenAI
    ENABLE_OPENAI_API,
    ONEDRIVE_CLIENT_ID,
    OPENAI_API_BASE_URLS,
    OPENAI_API_KEYS,
    OPENAI_API_CONFIGS,
    # Direct Connections
    ENABLE_DIRECT_CONNECTIONS,
    # Tool Server Configs
    TOOL_SERVER_CONNECTIONS,
    # Code Execution
    ENABLE_CODE_EXECUTION,
    CODE_EXECUTION_ENGINE,
    CODE_EXECUTION_JUPYTER_URL,
    CODE_EXECUTION_JUPYTER_AUTH,
    CODE_EXECUTION_JUPYTER_AUTH_TOKEN,
    CODE_EXECUTION_JUPYTER_AUTH_PASSWORD,
    CODE_EXECUTION_JUPYTER_TIMEOUT,
    ENABLE_CODE_INTERPRETER,
    CODE_INTERPRETER_ENGINE,
    CODE_INTERPRETER_PROMPT_TEMPLATE,
    CODE_INTERPRETER_JUPYTER_URL,
    CODE_INTERPRETER_JUPYTER_AUTH,
    CODE_INTERPRETER_JUPYTER_AUTH_TOKEN,
    CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD,
    CODE_INTERPRETER_JUPYTER_TIMEOUT,
    # Image
    AUTOMATIC1111_API_AUTH,
    AUTOMATIC1111_BASE_URL,
    AUTOMATIC1111_CFG_SCALE,
    AUTOMATIC1111_SAMPLER,
    AUTOMATIC1111_SCHEDULER,
    COMFYUI_BASE_URL,
    COMFYUI_API_KEY,
    COMFYUI_WORKFLOW,
    COMFYUI_WORKFLOW_NODES,
    ENABLE_IMAGE_GENERATION,
    ENABLE_IMAGE_PROMPT_GENERATION,
    IMAGE_GENERATION_ENGINE,
    IMAGE_GENERATION_MODEL,
    IMAGE_SIZE,
    IMAGE_STEPS,
    IMAGES_OPENAI_API_BASE_URL,
    IMAGES_OPENAI_API_KEY,
    IMAGES_GEMINI_API_BASE_URL,
    IMAGES_GEMINI_API_KEY,
    # Audio
    AUDIO_STT_ENGINE,
    AUDIO_STT_MODEL,
    AUDIO_STT_OPENAI_API_BASE_URL,
    AUDIO_STT_OPENAI_API_KEY,
    AUDIO_STT_AZURE_API_KEY,
    AUDIO_STT_AZURE_REGION,
    AUDIO_STT_AZURE_LOCALES,
    AUDIO_TTS_API_KEY,
    AUDIO_TTS_ENGINE,
    AUDIO_TTS_MODEL,
    AUDIO_TTS_OPENAI_API_BASE_URL,
    AUDIO_TTS_OPENAI_API_KEY,
    AUDIO_TTS_SPLIT_ON,
    AUDIO_TTS_VOICE,
    AUDIO_TTS_AZURE_SPEECH_REGION,
    AUDIO_TTS_AZURE_SPEECH_OUTPUT_FORMAT,
    PLAYWRIGHT_WS_URL,
    PLAYWRIGHT_TIMEOUT,
    FIRECRAWL_API_BASE_URL,
    FIRECRAWL_API_KEY,
    WEB_LOADER_ENGINE,
    WHISPER_MODEL,
    WHISPER_VAD_FILTER,
    DEEPGRAM_API_KEY,
    WHISPER_MODEL_AUTO_UPDATE,
    WHISPER_MODEL_DIR,
    # Retrieval
    RAG_TEMPLATE,
    DEFAULT_RAG_TEMPLATE,
    RAG_FULL_CONTEXT,
    BYPASS_EMBEDDING_AND_RETRIEVAL,
    RAG_EMBEDDING_MODEL,
    RAG_EMBEDDING_MODEL_AUTO_UPDATE,
    RAG_EMBEDDING_MODEL_TRUST_REMOTE_CODE,
    RAG_RERANKING_MODEL,
    RAG_RERANKING_MODEL_AUTO_UPDATE,
    RAG_RERANKING_MODEL_TRUST_REMOTE_CODE,
    RAG_EMBEDDING_ENGINE,
    RAG_EMBEDDING_BATCH_SIZE,
    RAG_RELEVANCE_THRESHOLD,
    RAG_FILE_MAX_COUNT,
    RAG_FILE_MAX_SIZE,
    RAG_OPENAI_API_BASE_URL,
    RAG_OPENAI_API_KEY,
    RAG_OLLAMA_BASE_URL,
    RAG_OLLAMA_API_KEY,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CONTENT_EXTRACTION_ENGINE,
    TIKA_SERVER_URL,
    DOCLING_SERVER_URL,
    DOCUMENT_INTELLIGENCE_ENDPOINT,
    DOCUMENT_INTELLIGENCE_KEY,
    MISTRAL_OCR_API_KEY,
    RAG_TOP_K,
    RAG_TOP_K_RERANKER,
    RAG_TEXT_SPLITTER,
    TIKTOKEN_ENCODING_NAME,
    PDF_EXTRACT_IMAGES,
    YOUTUBE_LOADER_LANGUAGE,
    YOUTUBE_LOADER_PROXY_URL,
    # Retrieval (Web Search)
    ENABLE_WEB_SEARCH,
    WEB_SEARCH_ENGINE,
    BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL,
    WEB_SEARCH_RESULT_COUNT,
    WEB_SEARCH_CONCURRENT_REQUESTS,
    WEB_SEARCH_TRUST_ENV,
    WEB_SEARCH_DOMAIN_FILTER_LIST,
    JINA_API_KEY,
    SEARCHAPI_API_KEY,
    SEARCHAPI_ENGINE,
    SERPAPI_API_KEY,
    SERPAPI_ENGINE,
    SEARXNG_QUERY_URL,
    SERPER_API_KEY,
    SERPLY_API_KEY,
    SERPSTACK_API_KEY,
    SERPSTACK_HTTPS,
    TAVILY_API_KEY,
    TAVILY_EXTRACT_DEPTH,
    BING_SEARCH_V7_ENDPOINT,
    BING_SEARCH_V7_SUBSCRIPTION_KEY,
    BRAVE_SEARCH_API_KEY,
    EXA_API_KEY,
    PERPLEXITY_API_KEY,
    SOUGOU_API_SID,
    SOUGOU_API_SK,
    KAGI_SEARCH_API_KEY,
    MOJEEK_SEARCH_API_KEY,
    BOCHA_SEARCH_API_KEY,
    GOOGLE_PSE_API_KEY,
    GOOGLE_PSE_ENGINE_ID,
    GOOGLE_DRIVE_CLIENT_ID,
    GOOGLE_DRIVE_API_KEY,
    ONEDRIVE_CLIENT_ID,
    ENABLE_RAG_HYBRID_SEARCH,
    ENABLE_RAG_LOCAL_WEB_FETCH,
    ENABLE_WEB_LOADER_SSL_VERIFICATION,
    ENABLE_GOOGLE_DRIVE_INTEGRATION,
    ENABLE_ONEDRIVE_INTEGRATION,
    UPLOAD_DIR,
    # WebUI
    WEBUI_AUTH,
    WEBUI_NAME,
    WEBUI_BANNERS,
    WEBHOOK_URL,
    ADMIN_EMAIL,
    SHOW_ADMIN_DETAILS,
    JWT_EXPIRES_IN,
    ENABLE_SIGNUP,
    ENABLE_LOGIN_FORM,
    ENABLE_API_KEY,
    ENABLE_API_KEY_ENDPOINT_RESTRICTIONS,
    API_KEY_ALLOWED_ENDPOINTS,
    ENABLE_CHANNELS,
    ENABLE_COMMUNITY_SHARING,
    ENABLE_MESSAGE_RATING,
    ENABLE_USER_WEBHOOKS,
    ENABLE_EVALUATION_ARENA_MODELS,
    USER_PERMISSIONS,
    DEFAULT_USER_ROLE,
    DEFAULT_PROMPT_SUGGESTIONS,
    DEFAULT_MODELS,
    DEFAULT_ARENA_MODEL,
    MODEL_ORDER_LIST,
    EVALUATION_ARENA_MODELS,
    # WebUI (OAuth)
    ENABLE_OAUTH_ROLE_MANAGEMENT,
    OAUTH_ROLES_CLAIM,
    OAUTH_EMAIL_CLAIM,
    OAUTH_PICTURE_CLAIM,
    OAUTH_USERNAME_CLAIM,
    OAUTH_ALLOWED_ROLES,
    OAUTH_ADMIN_ROLES,
    # WebUI (LDAP)
    ENABLE_LDAP,
    LDAP_SERVER_LABEL,
    LDAP_SERVER_HOST,
    LDAP_SERVER_PORT,
    LDAP_ATTRIBUTE_FOR_MAIL,
    LDAP_ATTRIBUTE_FOR_USERNAME,
    LDAP_SEARCH_FILTERS,
    LDAP_SEARCH_BASE,
    LDAP_APP_DN,
    LDAP_APP_PASSWORD,
    LDAP_USE_TLS,
    LDAP_CA_CERT_FILE,
    LDAP_CIPHERS,
    # Misc
    ENV,
    CACHE_DIR,
    STATIC_DIR,
    FRONTEND_BUILD_DIR,
    CORS_ALLOW_ORIGIN,
    DEFAULT_LOCALE,
    OAUTH_PROVIDERS,
    WEBUI_URL,
    # Admin
    ENABLE_ADMIN_CHAT_ACCESS,
    ENABLE_ADMIN_EXPORT,
    # Tasks
    TASK_MODEL,
    TASK_MODEL_EXTERNAL,
    ENABLE_TAGS_GENERATION,
    ENABLE_TITLE_GENERATION,
    ENABLE_SEARCH_QUERY_GENERATION,
    ENABLE_RETRIEVAL_QUERY_GENERATION,
    ENABLE_AUTOCOMPLETE_GENERATION,
    TITLE_GENERATION_PROMPT_TEMPLATE,
    TAGS_GENERATION_PROMPT_TEMPLATE,
    IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE,
    TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE,
    QUERY_GENERATION_PROMPT_TEMPLATE,
    AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE,
    AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH,
    AppConfig,
    reset_config,
)
from open_webui.env import (
    AUDIT_EXCLUDED_PATHS,
    AUDIT_LOG_LEVEL,
    CHANGELOG,
    REDIS_URL,
    REDIS_SENTINEL_HOSTS,
    REDIS_SENTINEL_PORT,
    GLOBAL_LOG_LEVEL,
    MAX_BODY_LOG_SIZE,
    SAFE_MODE,
    SRC_LOG_LEVELS,
    VERSION,
    WEBUI_BUILD_HASH,
    WEBUI_SECRET_KEY,
    WEBUI_SESSION_COOKIE_SAME_SITE,
    WEBUI_SESSION_COOKIE_SECURE,
    WEBUI_AUTH_TRUSTED_EMAIL_HEADER,
    WEBUI_AUTH_TRUSTED_NAME_HEADER,
    ENABLE_WEBSOCKET_SUPPORT,
    BYPASS_MODEL_ACCESS_CONTROL,
    RESET_CONFIG_ON_START,
    OFFLINE_MODE,
    ENABLE_OTEL,
    EXTERNAL_PWA_MANIFEST_URL,
)


from open_webui.utils.models import (
    get_all_models,
    get_all_base_models,
    check_model_access,
)
from open_webui.utils.chat import (
    generate_chat_completion as chat_completion_handler,
    chat_completed as chat_completed_handler,
    chat_action as chat_action_handler,
)
from open_webui.utils.middleware import process_chat_payload, process_chat_response
from open_webui.utils.access_control import has_access

from open_webui.utils.auth import (
    get_license_data,
    get_http_authorization_cred,
    decode_token,
    get_admin_user,
    get_verified_user,
)
from open_webui.utils.oauth import OAuthManager
from open_webui.utils.security_headers import SecurityHeadersMiddleware

from open_webui.tasks import (
    list_task_ids_by_chat_id,
    stop_task,
    list_tasks,
)  # Import from tasks.py

from open_webui.utils.redis import get_sentinels_from_env


if SAFE_MODE:
    print("SAFE MODE ENABLED")
    Functions.deactivate_all_functions()

logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                if path.endswith(".js"):
                    # Return 404 for javascript files
                    raise ex
                else:
                    return await super().get_response("index.html", scope)
            else:
                raise ex


print(
    rf"""
 ██████╗ ██████╗ ███████╗███╗   ██╗    ██╗    ██╗███████╗██████╗ ██╗   ██╗██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██║    ██║██╔════╝██╔══██╗██║   ██║██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║    ██║ █╗ ██║█████╗  ██████╔╝██║   ██║██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ██║███╗██║██╔══╝  ██╔══██╗██║   ██║██║
╚██████╔╝██║     ███████╗██║ ╚████║    ╚███╔███╔╝███████╗██████╔╝╚██████╔╝██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝     ╚══╝╚══╝ ╚══════╝╚═════╝  ╚═════╝ ╚═╝


v{VERSION} - building the best open-source AI user interface.
{f"Commit: {WEBUI_BUILD_HASH}" if WEBUI_BUILD_HASH != "dev-build" else ""}
https://github.com/open-webui/open-webui
"""
)
# === Setup ===
# Dynamically load BASE_DIR from base_dir.txt
# This allows flexible file paths across multiple systems
# Files include: personality, conversation log, memory db, etc.

import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load base directory path
try:
    with open(os.path.join(SCRIPT_DIR, "base_dir.txt"), "r", encoding="utf-8") as f:
        BASE_DIR = f.read().strip()
except Exception as e:
    raise RuntimeError(f"❌ Could not load base_dir.txt: {e}")

# Static personality file remains outside the DB
PERSONALITY_FILE = os.path.join(BASE_DIR, "personality_amicia.txt")
with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
    personality = f.read().strip()


# Connect to SQLite memory DB
DB_PATH = os.path.join(BASE_DIR, "ai_memory.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create required tables if they don't exist
cursor.executescript("""
CREATE TABLE IF NOT EXISTS user_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    type TEXT,            -- e.g. 'like', 'dislike'
    value TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS people (
    name TEXT PRIMARY KEY,
    info TEXT
);

CREATE TABLE IF NOT EXISTS convo_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    ai TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS ai_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,       -- 'like' or 'dislike'
    value TEXT       -- the actual item (e.g., "card magic")
);


CREATE TABLE IF NOT EXISTS last_seen (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    timestamp TEXT
);
""")

conn.commit()

def remember_user_like(item: str):
    cursor.execute("INSERT OR IGNORE INTO user_memory (category, type, value) VALUES (?, ?, ?)", ("general", "like", item.strip()))
    conn.commit()

def remember_user_dislike(item: str):
    cursor.execute("INSERT OR IGNORE INTO user_memory (category, type, value) VALUES (?, ?, ?)", ("general", "dislike", item.strip()))
    conn.commit()

def get_user_memory_summary():
    try:
        cursor.execute("SELECT type, value FROM user_memory")
        rows = cursor.fetchall()

        likes = [val for typ, val in rows if typ == "like"][:2]
        dislikes = [val for typ, val in rows if typ == "dislike"][:2]

        summary = []
        if likes:
            summary.append(f"She knows the user enjoys things like {', '.join(likes)}.")
        if dislikes:
            summary.append(f"She also remembers the user prefers to avoid topics like {', '.join(dislikes)}.")
        return " ".join(summary)
    except Exception as e:
        print(f"⚠️ DB read error in get_user_memory_summary: {e}")
        return ""

def remember_ai_like(item: str):
    cursor.execute("INSERT OR IGNORE INTO ai_memory (type, value) VALUES (?, ?)", ("like", item.strip()))
    conn.commit()

def remember_ai_dislike(item: str):
    cursor.execute("INSERT OR IGNORE INTO ai_memory (type, value) VALUES (?, ?)", ("dislike", item.strip()))
    conn.commit()

    
    
def get_ai_memory_summary():
    try:
        cursor.execute("SELECT type, value FROM ai_memory")
        rows = cursor.fetchall()
        likes = [val for typ, val in rows if typ == "like"][:2]
        dislikes = [val for typ, val in rows if typ == "dislike"][:2]

        summary = []
        if likes:
            summary.append(f"Amicia enjoys things like {', '.join(likes)}.")
        if dislikes:
            summary.append(f"She dislikes topics like {', '.join(dislikes)}.")
        return " ".join(summary)
    except Exception as e:
        print(f"⚠️ DB error in get_ai_memory_summary: {e}")
        return ""



def remember_person(name: str, description: str):
    try:
        cursor.execute("INSERT OR REPLACE INTO people (name, info) VALUES (?, ?)", (name.strip(), description.strip()))
        conn.commit()
    except Exception as e:
        print(f"⚠️ DB error in remember_person: {e}")

def get_known_people_summary():
    try:
        cursor.execute("SELECT name, info FROM people")
        rows = cursor.fetchall()
        if not rows:
            return ""
        entries = [f"{name}: {info}" for name, info in rows]
        return "People she remembers:\n" + "\n".join(entries)
    except Exception as e:
        print(f"⚠️ DB error in get_known_people_summary: {e}")
        return ""





@asynccontextmanager
async def lifespan(app: FastAPI):
    start_logger()
    if RESET_CONFIG_ON_START:
        reset_config()

    if LICENSE_KEY:
        get_license_data(app, LICENSE_KEY)

    asyncio.create_task(periodic_usage_pool_cleanup())
    yield


app = FastAPI(
    title="Open WebUI",
    docs_url="/docs" if ENV == "dev" else None,
    openapi_url="/openapi.json" if ENV == "dev" else None,
    redoc_url=None,
    lifespan=lifespan,
)

oauth_manager = OAuthManager(app)

app.state.config = AppConfig(
    redis_url=REDIS_URL,
    redis_sentinels=get_sentinels_from_env(REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT),
)

app.state.WEBUI_NAME = WEBUI_NAME
app.state.LICENSE_METADATA = None


########################################
#
# OPENTELEMETRY
#
########################################

if ENABLE_OTEL:
    from open_webui.utils.telemetry.setup import setup as setup_opentelemetry

    setup_opentelemetry(app=app, db_engine=engine)


########################################
#
# OLLAMA
#
########################################


app.state.config.ENABLE_OLLAMA_API = ENABLE_OLLAMA_API
app.state.config.OLLAMA_BASE_URLS = OLLAMA_BASE_URLS
app.state.config.OLLAMA_API_CONFIGS = OLLAMA_API_CONFIGS

app.state.OLLAMA_MODELS = {}

########################################
#
# OPENAI
#
########################################

app.state.config.ENABLE_OPENAI_API = ENABLE_OPENAI_API
app.state.config.OPENAI_API_BASE_URLS = OPENAI_API_BASE_URLS
app.state.config.OPENAI_API_KEYS = OPENAI_API_KEYS
app.state.config.OPENAI_API_CONFIGS = OPENAI_API_CONFIGS

app.state.OPENAI_MODELS = {}

########################################
#
# TOOL SERVERS
#
########################################

app.state.config.TOOL_SERVER_CONNECTIONS = TOOL_SERVER_CONNECTIONS
app.state.TOOL_SERVERS = []

########################################
#
# DIRECT CONNECTIONS
#
########################################

app.state.config.ENABLE_DIRECT_CONNECTIONS = ENABLE_DIRECT_CONNECTIONS

########################################
#
# WEBUI
#
########################################

app.state.config.WEBUI_URL = WEBUI_URL
app.state.config.ENABLE_SIGNUP = ENABLE_SIGNUP
app.state.config.ENABLE_LOGIN_FORM = ENABLE_LOGIN_FORM

app.state.config.ENABLE_API_KEY = ENABLE_API_KEY
app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS = (
    ENABLE_API_KEY_ENDPOINT_RESTRICTIONS
)
app.state.config.API_KEY_ALLOWED_ENDPOINTS = API_KEY_ALLOWED_ENDPOINTS

app.state.config.JWT_EXPIRES_IN = JWT_EXPIRES_IN

app.state.config.SHOW_ADMIN_DETAILS = SHOW_ADMIN_DETAILS
app.state.config.ADMIN_EMAIL = ADMIN_EMAIL


app.state.config.DEFAULT_MODELS = DEFAULT_MODELS
app.state.config.DEFAULT_PROMPT_SUGGESTIONS = DEFAULT_PROMPT_SUGGESTIONS
app.state.config.DEFAULT_USER_ROLE = DEFAULT_USER_ROLE

app.state.config.USER_PERMISSIONS = USER_PERMISSIONS
app.state.config.WEBHOOK_URL = WEBHOOK_URL
app.state.config.BANNERS = WEBUI_BANNERS
app.state.config.MODEL_ORDER_LIST = MODEL_ORDER_LIST


app.state.config.ENABLE_CHANNELS = ENABLE_CHANNELS
app.state.config.ENABLE_COMMUNITY_SHARING = ENABLE_COMMUNITY_SHARING
app.state.config.ENABLE_MESSAGE_RATING = ENABLE_MESSAGE_RATING
app.state.config.ENABLE_USER_WEBHOOKS = ENABLE_USER_WEBHOOKS

app.state.config.ENABLE_EVALUATION_ARENA_MODELS = ENABLE_EVALUATION_ARENA_MODELS
app.state.config.EVALUATION_ARENA_MODELS = EVALUATION_ARENA_MODELS

app.state.config.OAUTH_USERNAME_CLAIM = OAUTH_USERNAME_CLAIM
app.state.config.OAUTH_PICTURE_CLAIM = OAUTH_PICTURE_CLAIM
app.state.config.OAUTH_EMAIL_CLAIM = OAUTH_EMAIL_CLAIM

app.state.config.ENABLE_OAUTH_ROLE_MANAGEMENT = ENABLE_OAUTH_ROLE_MANAGEMENT
app.state.config.OAUTH_ROLES_CLAIM = OAUTH_ROLES_CLAIM
app.state.config.OAUTH_ALLOWED_ROLES = OAUTH_ALLOWED_ROLES
app.state.config.OAUTH_ADMIN_ROLES = OAUTH_ADMIN_ROLES

app.state.config.ENABLE_LDAP = ENABLE_LDAP
app.state.config.LDAP_SERVER_LABEL = LDAP_SERVER_LABEL
app.state.config.LDAP_SERVER_HOST = LDAP_SERVER_HOST
app.state.config.LDAP_SERVER_PORT = LDAP_SERVER_PORT
app.state.config.LDAP_ATTRIBUTE_FOR_MAIL = LDAP_ATTRIBUTE_FOR_MAIL
app.state.config.LDAP_ATTRIBUTE_FOR_USERNAME = LDAP_ATTRIBUTE_FOR_USERNAME
app.state.config.LDAP_APP_DN = LDAP_APP_DN
app.state.config.LDAP_APP_PASSWORD = LDAP_APP_PASSWORD
app.state.config.LDAP_SEARCH_BASE = LDAP_SEARCH_BASE
app.state.config.LDAP_SEARCH_FILTERS = LDAP_SEARCH_FILTERS
app.state.config.LDAP_USE_TLS = LDAP_USE_TLS
app.state.config.LDAP_CA_CERT_FILE = LDAP_CA_CERT_FILE
app.state.config.LDAP_CIPHERS = LDAP_CIPHERS


app.state.AUTH_TRUSTED_EMAIL_HEADER = WEBUI_AUTH_TRUSTED_EMAIL_HEADER
app.state.AUTH_TRUSTED_NAME_HEADER = WEBUI_AUTH_TRUSTED_NAME_HEADER
app.state.EXTERNAL_PWA_MANIFEST_URL = EXTERNAL_PWA_MANIFEST_URL

app.state.USER_COUNT = None
app.state.TOOLS = {}
app.state.FUNCTIONS = {}

########################################
#
# RETRIEVAL
#
########################################


app.state.config.TOP_K = RAG_TOP_K
app.state.config.TOP_K_RERANKER = RAG_TOP_K_RERANKER
app.state.config.RELEVANCE_THRESHOLD = RAG_RELEVANCE_THRESHOLD
app.state.config.FILE_MAX_SIZE = RAG_FILE_MAX_SIZE
app.state.config.FILE_MAX_COUNT = RAG_FILE_MAX_COUNT


app.state.config.RAG_FULL_CONTEXT = RAG_FULL_CONTEXT
app.state.config.BYPASS_EMBEDDING_AND_RETRIEVAL = BYPASS_EMBEDDING_AND_RETRIEVAL
app.state.config.ENABLE_RAG_HYBRID_SEARCH = ENABLE_RAG_HYBRID_SEARCH
app.state.config.ENABLE_WEB_LOADER_SSL_VERIFICATION = ENABLE_WEB_LOADER_SSL_VERIFICATION

app.state.config.CONTENT_EXTRACTION_ENGINE = CONTENT_EXTRACTION_ENGINE
app.state.config.TIKA_SERVER_URL = TIKA_SERVER_URL
app.state.config.DOCLING_SERVER_URL = DOCLING_SERVER_URL
app.state.config.DOCUMENT_INTELLIGENCE_ENDPOINT = DOCUMENT_INTELLIGENCE_ENDPOINT
app.state.config.DOCUMENT_INTELLIGENCE_KEY = DOCUMENT_INTELLIGENCE_KEY
app.state.config.MISTRAL_OCR_API_KEY = MISTRAL_OCR_API_KEY

app.state.config.TEXT_SPLITTER = RAG_TEXT_SPLITTER
app.state.config.TIKTOKEN_ENCODING_NAME = TIKTOKEN_ENCODING_NAME

app.state.config.CHUNK_SIZE = CHUNK_SIZE
app.state.config.CHUNK_OVERLAP = CHUNK_OVERLAP

app.state.config.RAG_EMBEDDING_ENGINE = RAG_EMBEDDING_ENGINE
app.state.config.RAG_EMBEDDING_MODEL = RAG_EMBEDDING_MODEL
app.state.config.RAG_EMBEDDING_BATCH_SIZE = RAG_EMBEDDING_BATCH_SIZE
app.state.config.RAG_RERANKING_MODEL = RAG_RERANKING_MODEL
app.state.config.RAG_TEMPLATE = RAG_TEMPLATE

app.state.config.RAG_OPENAI_API_BASE_URL = RAG_OPENAI_API_BASE_URL
app.state.config.RAG_OPENAI_API_KEY = RAG_OPENAI_API_KEY

app.state.config.RAG_OLLAMA_BASE_URL = RAG_OLLAMA_BASE_URL
app.state.config.RAG_OLLAMA_API_KEY = RAG_OLLAMA_API_KEY

app.state.config.PDF_EXTRACT_IMAGES = PDF_EXTRACT_IMAGES

app.state.config.YOUTUBE_LOADER_LANGUAGE = YOUTUBE_LOADER_LANGUAGE
app.state.config.YOUTUBE_LOADER_PROXY_URL = YOUTUBE_LOADER_PROXY_URL


app.state.config.ENABLE_WEB_SEARCH = ENABLE_WEB_SEARCH
app.state.config.WEB_SEARCH_ENGINE = WEB_SEARCH_ENGINE
app.state.config.WEB_SEARCH_DOMAIN_FILTER_LIST = WEB_SEARCH_DOMAIN_FILTER_LIST
app.state.config.WEB_SEARCH_RESULT_COUNT = WEB_SEARCH_RESULT_COUNT
app.state.config.WEB_SEARCH_CONCURRENT_REQUESTS = WEB_SEARCH_CONCURRENT_REQUESTS
app.state.config.WEB_LOADER_ENGINE = WEB_LOADER_ENGINE
app.state.config.WEB_SEARCH_TRUST_ENV = WEB_SEARCH_TRUST_ENV
app.state.config.BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL = (
    BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL
)

app.state.config.ENABLE_GOOGLE_DRIVE_INTEGRATION = ENABLE_GOOGLE_DRIVE_INTEGRATION
app.state.config.ENABLE_ONEDRIVE_INTEGRATION = ENABLE_ONEDRIVE_INTEGRATION
app.state.config.SEARXNG_QUERY_URL = SEARXNG_QUERY_URL
app.state.config.GOOGLE_PSE_API_KEY = GOOGLE_PSE_API_KEY
app.state.config.GOOGLE_PSE_ENGINE_ID = GOOGLE_PSE_ENGINE_ID
app.state.config.BRAVE_SEARCH_API_KEY = BRAVE_SEARCH_API_KEY
app.state.config.KAGI_SEARCH_API_KEY = KAGI_SEARCH_API_KEY
app.state.config.MOJEEK_SEARCH_API_KEY = MOJEEK_SEARCH_API_KEY
app.state.config.BOCHA_SEARCH_API_KEY = BOCHA_SEARCH_API_KEY
app.state.config.SERPSTACK_API_KEY = SERPSTACK_API_KEY
app.state.config.SERPSTACK_HTTPS = SERPSTACK_HTTPS
app.state.config.SERPER_API_KEY = SERPER_API_KEY
app.state.config.SERPLY_API_KEY = SERPLY_API_KEY
app.state.config.TAVILY_API_KEY = TAVILY_API_KEY
app.state.config.SEARCHAPI_API_KEY = SEARCHAPI_API_KEY
app.state.config.SEARCHAPI_ENGINE = SEARCHAPI_ENGINE
app.state.config.SERPAPI_API_KEY = SERPAPI_API_KEY
app.state.config.SERPAPI_ENGINE = SERPAPI_ENGINE
app.state.config.JINA_API_KEY = JINA_API_KEY
app.state.config.BING_SEARCH_V7_ENDPOINT = BING_SEARCH_V7_ENDPOINT
app.state.config.BING_SEARCH_V7_SUBSCRIPTION_KEY = BING_SEARCH_V7_SUBSCRIPTION_KEY
app.state.config.EXA_API_KEY = EXA_API_KEY
app.state.config.PERPLEXITY_API_KEY = PERPLEXITY_API_KEY
app.state.config.SOUGOU_API_SID = SOUGOU_API_SID
app.state.config.SOUGOU_API_SK = SOUGOU_API_SK


app.state.config.PLAYWRIGHT_WS_URL = PLAYWRIGHT_WS_URL
app.state.config.PLAYWRIGHT_TIMEOUT = PLAYWRIGHT_TIMEOUT
app.state.config.FIRECRAWL_API_BASE_URL = FIRECRAWL_API_BASE_URL
app.state.config.FIRECRAWL_API_KEY = FIRECRAWL_API_KEY
app.state.config.TAVILY_EXTRACT_DEPTH = TAVILY_EXTRACT_DEPTH

app.state.EMBEDDING_FUNCTION = None
app.state.ef = None
app.state.rf = None

app.state.YOUTUBE_LOADER_TRANSLATION = None


try:
    app.state.ef = get_ef(
        app.state.config.RAG_EMBEDDING_ENGINE,
        app.state.config.RAG_EMBEDDING_MODEL,
        RAG_EMBEDDING_MODEL_AUTO_UPDATE,
    )

    app.state.rf = get_rf(
        app.state.config.RAG_RERANKING_MODEL,
        RAG_RERANKING_MODEL_AUTO_UPDATE,
    )
except Exception as e:
    log.error(f"Error updating models: {e}")
    pass


app.state.EMBEDDING_FUNCTION = get_embedding_function(
    app.state.config.RAG_EMBEDDING_ENGINE,
    app.state.config.RAG_EMBEDDING_MODEL,
    app.state.ef,
    (
        app.state.config.RAG_OPENAI_API_BASE_URL
        if app.state.config.RAG_EMBEDDING_ENGINE == "openai"
        else app.state.config.RAG_OLLAMA_BASE_URL
    ),
    (
        app.state.config.RAG_OPENAI_API_KEY
        if app.state.config.RAG_EMBEDDING_ENGINE == "openai"
        else app.state.config.RAG_OLLAMA_API_KEY
    ),
    app.state.config.RAG_EMBEDDING_BATCH_SIZE,
)

########################################
#
# CODE EXECUTION
#
########################################

app.state.config.ENABLE_CODE_EXECUTION = ENABLE_CODE_EXECUTION
app.state.config.CODE_EXECUTION_ENGINE = CODE_EXECUTION_ENGINE
app.state.config.CODE_EXECUTION_JUPYTER_URL = CODE_EXECUTION_JUPYTER_URL
app.state.config.CODE_EXECUTION_JUPYTER_AUTH = CODE_EXECUTION_JUPYTER_AUTH
app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN = CODE_EXECUTION_JUPYTER_AUTH_TOKEN
app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD = (
    CODE_EXECUTION_JUPYTER_AUTH_PASSWORD
)
app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT = CODE_EXECUTION_JUPYTER_TIMEOUT

app.state.config.ENABLE_CODE_INTERPRETER = ENABLE_CODE_INTERPRETER
app.state.config.CODE_INTERPRETER_ENGINE = CODE_INTERPRETER_ENGINE
app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE = CODE_INTERPRETER_PROMPT_TEMPLATE

app.state.config.CODE_INTERPRETER_JUPYTER_URL = CODE_INTERPRETER_JUPYTER_URL
app.state.config.CODE_INTERPRETER_JUPYTER_AUTH = CODE_INTERPRETER_JUPYTER_AUTH
app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN = (
    CODE_INTERPRETER_JUPYTER_AUTH_TOKEN
)
app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD = (
    CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD
)
app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT = CODE_INTERPRETER_JUPYTER_TIMEOUT

########################################
#
# IMAGES
#
########################################

app.state.config.IMAGE_GENERATION_ENGINE = IMAGE_GENERATION_ENGINE
app.state.config.ENABLE_IMAGE_GENERATION = ENABLE_IMAGE_GENERATION
app.state.config.ENABLE_IMAGE_PROMPT_GENERATION = ENABLE_IMAGE_PROMPT_GENERATION

app.state.config.IMAGES_OPENAI_API_BASE_URL = IMAGES_OPENAI_API_BASE_URL
app.state.config.IMAGES_OPENAI_API_KEY = IMAGES_OPENAI_API_KEY

app.state.config.IMAGES_GEMINI_API_BASE_URL = IMAGES_GEMINI_API_BASE_URL
app.state.config.IMAGES_GEMINI_API_KEY = IMAGES_GEMINI_API_KEY

app.state.config.IMAGE_GENERATION_MODEL = IMAGE_GENERATION_MODEL

app.state.config.AUTOMATIC1111_BASE_URL = AUTOMATIC1111_BASE_URL
app.state.config.AUTOMATIC1111_API_AUTH = AUTOMATIC1111_API_AUTH
app.state.config.AUTOMATIC1111_CFG_SCALE = AUTOMATIC1111_CFG_SCALE
app.state.config.AUTOMATIC1111_SAMPLER = AUTOMATIC1111_SAMPLER
app.state.config.AUTOMATIC1111_SCHEDULER = AUTOMATIC1111_SCHEDULER
app.state.config.COMFYUI_BASE_URL = COMFYUI_BASE_URL
app.state.config.COMFYUI_API_KEY = COMFYUI_API_KEY
app.state.config.COMFYUI_WORKFLOW = COMFYUI_WORKFLOW
app.state.config.COMFYUI_WORKFLOW_NODES = COMFYUI_WORKFLOW_NODES

app.state.config.IMAGE_SIZE = IMAGE_SIZE
app.state.config.IMAGE_STEPS = IMAGE_STEPS


########################################
#
# AUDIO
#
########################################

app.state.config.STT_OPENAI_API_BASE_URL = AUDIO_STT_OPENAI_API_BASE_URL
app.state.config.STT_OPENAI_API_KEY = AUDIO_STT_OPENAI_API_KEY
app.state.config.STT_ENGINE = AUDIO_STT_ENGINE
app.state.config.STT_MODEL = AUDIO_STT_MODEL

app.state.config.WHISPER_MODEL = WHISPER_MODEL
app.state.config.WHISPER_VAD_FILTER = WHISPER_VAD_FILTER
app.state.config.DEEPGRAM_API_KEY = DEEPGRAM_API_KEY

app.state.config.AUDIO_STT_AZURE_API_KEY = AUDIO_STT_AZURE_API_KEY
app.state.config.AUDIO_STT_AZURE_REGION = AUDIO_STT_AZURE_REGION
app.state.config.AUDIO_STT_AZURE_LOCALES = AUDIO_STT_AZURE_LOCALES

app.state.config.TTS_OPENAI_API_BASE_URL = AUDIO_TTS_OPENAI_API_BASE_URL
app.state.config.TTS_OPENAI_API_KEY = AUDIO_TTS_OPENAI_API_KEY
app.state.config.TTS_ENGINE = AUDIO_TTS_ENGINE
app.state.config.TTS_MODEL = AUDIO_TTS_MODEL
app.state.config.TTS_VOICE = AUDIO_TTS_VOICE
app.state.config.TTS_API_KEY = AUDIO_TTS_API_KEY
app.state.config.TTS_SPLIT_ON = AUDIO_TTS_SPLIT_ON


app.state.config.TTS_AZURE_SPEECH_REGION = AUDIO_TTS_AZURE_SPEECH_REGION
app.state.config.TTS_AZURE_SPEECH_OUTPUT_FORMAT = AUDIO_TTS_AZURE_SPEECH_OUTPUT_FORMAT


app.state.faster_whisper_model = None
app.state.speech_synthesiser = None
app.state.speech_speaker_embeddings_dataset = None


########################################
#
# TASKS
#
########################################


app.state.config.TASK_MODEL = TASK_MODEL
app.state.config.TASK_MODEL_EXTERNAL = TASK_MODEL_EXTERNAL


app.state.config.ENABLE_SEARCH_QUERY_GENERATION = ENABLE_SEARCH_QUERY_GENERATION
app.state.config.ENABLE_RETRIEVAL_QUERY_GENERATION = ENABLE_RETRIEVAL_QUERY_GENERATION
app.state.config.ENABLE_AUTOCOMPLETE_GENERATION = ENABLE_AUTOCOMPLETE_GENERATION
app.state.config.ENABLE_TAGS_GENERATION = ENABLE_TAGS_GENERATION
app.state.config.ENABLE_TITLE_GENERATION = ENABLE_TITLE_GENERATION


app.state.config.TITLE_GENERATION_PROMPT_TEMPLATE = TITLE_GENERATION_PROMPT_TEMPLATE
app.state.config.TAGS_GENERATION_PROMPT_TEMPLATE = TAGS_GENERATION_PROMPT_TEMPLATE
app.state.config.IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE = (
    IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE
)

app.state.config.TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE = (
    TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE
)
app.state.config.QUERY_GENERATION_PROMPT_TEMPLATE = QUERY_GENERATION_PROMPT_TEMPLATE
app.state.config.AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE = (
    AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE
)
app.state.config.AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH = (
    AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH
)


########################################
#
# WEBUI
#
########################################

app.state.MODELS = {}


class RedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if the request is a GET request
        if request.method == "GET":
            path = request.url.path
            query_params = dict(parse_qs(urlparse(str(request.url)).query))

            # Check for the specific watch path and the presence of 'v' parameter
            if path.endswith("/watch") and "v" in query_params:
                video_id = query_params["v"][0]  # Extract the first 'v' parameter
                encoded_video_id = urlencode({"youtube": video_id})
                redirect_url = f"/?{encoded_video_id}"
                return RedirectResponse(url=redirect_url)

        # Proceed with the normal flow of other requests
        response = await call_next(request)
        return response


# Add the middleware to the app
app.add_middleware(RedirectMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

def update_timestamp():
    now = datetime.now(pytz.timezone("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR REPLACE INTO last_seen (id, timestamp) VALUES (1, ?)", (now,))
    conn.commit()

        
def get_time_since_last_visit(threshold_hours=3):
    try:
        cursor.execute("SELECT timestamp FROM last_seen WHERE id = 1")
        row = cursor.fetchone()
        if not row:
            return ""

        # Parse as naive and localize it to the correct timezone
        tz = pytz.timezone("America/Chicago")
        last_seen = tz.localize(datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"))

        # Now get current time with the same timezone
        now = datetime.now(tz)
        diff = now - last_seen

        minutes = int(diff.total_seconds() // 60)
        hours = minutes // 60

        if hours >= threshold_hours:
            if hours >= 24:
                return f"It’s been {hours // 24} day(s) and {hours % 24} hour(s) since your last visit."
            else:
                return f"It’s been {hours} hour(s) and {minutes % 60} minutes since your last visit."
        else:
            return ""

    except Exception as e:
        print(f"⚠️ Error reading last_seen: {e}")
        return ""


        

def get_today_date():
    now = datetime.now(pytz.timezone("America/Chicago"))  # Change timezone if needed
    return now.strftime("Today is %A, %B %d, %Y. The time is %I:%M %p.")

def log_conversation(user_input: str, ai_output: str):
    try:
        cursor.execute(
            "INSERT INTO convo_log (user, ai, timestamp) VALUES (?, ?, ?)",
            (user_input.strip(), ai_output.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    except Exception as e:
        print(f"⚠️ Failed to log conversation: {e}")


def trim(text: str, limit: int = 250) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "..."
    
def get_recent_convo_for_prompt(count=5):
    entries = pull_conversation(count)
    lines = []
    for user, ai in entries:
        lines.append(f"User: {user}")
        lines.append(f"AI: {ai}")
    return "\n".join(lines)


def pull_conversation(count=20):
    try:
        cursor.execute("SELECT user, ai FROM convo_log ORDER BY id DESC LIMIT ?", (count,))
        return cursor.fetchall()[::-1]  # reverse to maintain original order
    except Exception as e:
        print(f"⚠️ Error pulling conversation: {e}")
        return []


import wikipedia
import requests
from bs4 import BeautifulSoup

async def search_web(query: str):
    print(f"🔎 Searching Wikipedia for: {query}")
    wikipedia.set_lang("en")

    try:
        summary = wikipedia.summary(query, sentences=2)
        return f"{summary}\n\n(Source: Wikipedia)"
    
    except wikipedia.exceptions.DisambiguationError as e:
        options = ', '.join(e.options[:3])
        print(f"Too many meanings: {options}")
        return f"That term is too broad. Did you mean: {options}?"

    except wikipedia.exceptions.PageError:
        print("📄 Wikipedia page not found. Falling back to DuckDuckGo...")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            params = {"q": query}
            response = requests.get("https://html.duckduckgo.com/html/", headers=headers, params=params)
            soup = BeautifulSoup(response.text, "html.parser")
            result = soup.find("a", class_="result__a")
            snippet = result.get_text(strip=True) if result else None
            return snippet or "DuckDuckGo returned no clear answer."
        except Exception as e:
            return f"Search failed entirely: {e}"
    
    except Exception as e:
        return f"Search failed: {e}"


        


@app.middleware("http")
async def commit_session_after_request(request: Request, call_next):
    response = await call_next(request)
    # log.debug("Commit session after request")
    Session.commit()
    return response


@app.middleware("http")
async def check_url(request: Request, call_next):
    start_time = int(time.time())
    request.state.token = get_http_authorization_cred(
        request.headers.get("Authorization")
    )

    request.state.enable_api_key = app.state.config.ENABLE_API_KEY
    response = await call_next(request)
    process_time = int(time.time()) - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def inspect_websocket(request: Request, call_next):
    if (
        "/ws/socket.io" in request.url.path
        and request.query_params.get("transport") == "websocket"
    ):
        upgrade = (request.headers.get("Upgrade") or "").lower()
        connection = (request.headers.get("Connection") or "").lower().split(",")
        # Check that there's the correct headers for an upgrade, else reject the connection
        # This is to work around this upstream issue: https://github.com/miguelgrinberg/python-engineio/issues/367
        if upgrade != "websocket" or "upgrade" not in connection:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid WebSocket upgrade request"},
            )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/ws", socket_app)


app.include_router(ollama.router, prefix="/ollama", tags=["ollama"])
app.include_router(openai.router, prefix="/openai", tags=["openai"])


app.include_router(pipelines.router, prefix="/api/v1/pipelines", tags=["pipelines"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(images.router, prefix="/api/v1/images", tags=["images"])

app.include_router(audio.router, prefix="/api/v1/audio", tags=["audio"])
app.include_router(retrieval.router, prefix="/api/v1/retrieval", tags=["retrieval"])

app.include_router(configs.router, prefix="/api/v1/configs", tags=["configs"])

app.include_router(auths.router, prefix="/api/v1/auths", tags=["auths"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


app.include_router(channels.router, prefix="/api/v1/channels", tags=["channels"])
app.include_router(chats.router, prefix="/api/v1/chats", tags=["chats"])

app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["prompts"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])

app.include_router(memories.router, prefix="/api/v1/memories", tags=["memories"])
app.include_router(folders.router, prefix="/api/v1/folders", tags=["folders"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(functions.router, prefix="/api/v1/functions", tags=["functions"])
app.include_router(
    evaluations.router, prefix="/api/v1/evaluations", tags=["evaluations"]
)
app.include_router(utils.router, prefix="/api/v1/utils", tags=["utils"])


try:
    audit_level = AuditLevel(AUDIT_LOG_LEVEL)
except ValueError as e:
    logger.error(f"Invalid audit level: {AUDIT_LOG_LEVEL}. Error: {e}")
    audit_level = AuditLevel.NONE

if audit_level != AuditLevel.NONE:
    app.add_middleware(
        AuditLoggingMiddleware,
        audit_level=audit_level,
        excluded_paths=AUDIT_EXCLUDED_PATHS,
        max_body_size=MAX_BODY_LOG_SIZE,
    )
##################################
#
# Chat Endpoints
#
##################################


@app.get("/api/models")
async def get_models(request: Request, user=Depends(get_verified_user)):
    def get_filtered_models(models, user):
        filtered_models = []
        for model in models:
            if model.get("arena"):
                if has_access(
                    user.id,
                    type="read",
                    access_control=model.get("info", {})
                    .get("meta", {})
                    .get("access_control", {}),
                ):
                    filtered_models.append(model)
                continue

            model_info = Models.get_model_by_id(model["id"])
            if model_info:
                if user.id == model_info.user_id or has_access(
                    user.id, type="read", access_control=model_info.access_control
                ):
                    filtered_models.append(model)

        return filtered_models

    all_models = await get_all_models(request, user=user)

    models = []
    for model in all_models:
        # Filter out filter pipelines
        if "pipeline" in model and model["pipeline"].get("type", None) == "filter":
            continue

        try:
            model_tags = [
                tag.get("name")
                for tag in model.get("info", {}).get("meta", {}).get("tags", [])
            ]
            tags = [tag.get("name") for tag in model.get("tags", [])]

            tags = list(set(model_tags + tags))
            model["tags"] = [{"name": tag} for tag in tags]
        except Exception as e:
            log.debug(f"Error processing model tags: {e}")
            model["tags"] = []
            pass

        models.append(model)

    model_order_list = request.app.state.config.MODEL_ORDER_LIST
    if model_order_list:
        model_order_dict = {model_id: i for i, model_id in enumerate(model_order_list)}
        # Sort models by order list priority, with fallback for those not in the list
        models.sort(
            key=lambda x: (model_order_dict.get(x["id"], float("inf")), x["name"])
        )

    # Filter out models that the user does not have access to
    if user.role == "user" and not BYPASS_MODEL_ACCESS_CONTROL:
        models = get_filtered_models(models, user)

    log.debug(
        f"/api/models returned filtered models accessible to the user: {json.dumps([model['id'] for model in models])}"
    )
    return {"data": models}


@app.get("/api/models/base")
async def get_base_models(request: Request, user=Depends(get_admin_user)):
    models = await get_all_base_models(request, user=user)
    return {"data": models}


@app.post("/api/chat/completions")
async def chat_completion(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
):
    # Ensure that the models are loaded, and handle the model selection
    if not request.app.state.MODELS:
        await get_all_models(request, user=user)

    model_item = form_data.pop("model_item", {})
    tasks = form_data.pop("background_tasks", None)

    metadata = {}
    try:
        if not model_item.get("direct", False):
            model_id = form_data.get("model", None)
            if model_id not in request.app.state.MODELS:
                raise Exception("Model not found")

            model = request.app.state.MODELS[model_id]
            model_info = Models.get_model_by_id(model_id)

            if not BYPASS_MODEL_ACCESS_CONTROL and user.role == "user":
                check_model_access(user, model)
        else:
            model = model_item
            model_info = None
            request.state.direct = True
            request.state.model = model

        metadata = {
            "user_id": user.id,
            "chat_id": form_data.pop("chat_id", None),
            "message_id": form_data.pop("id", None),
            "session_id": form_data.pop("session_id", None),
            "tool_ids": form_data.get("tool_ids", None),
            "tool_servers": form_data.pop("tool_servers", None),
            "files": form_data.get("files", None),
            "features": form_data.get("features", None),
            "variables": form_data.get("variables", None),
            "model": model,
            "direct": model_item.get("direct", False),
        }

        request.state.metadata = metadata
        form_data["metadata"] = metadata

        form_data, metadata, events = await process_chat_payload(
            request, form_data, user, metadata, model
        )

    except Exception as e:
        log.debug(f"Error processing chat payload: {e}")
        if metadata.get("chat_id") and metadata.get("message_id"):
            Chats.upsert_message_to_chat_by_id_and_message_id(
                metadata["chat_id"],
                metadata["message_id"],
                {"error": {"content": str(e)}},
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Initialize ai_output at the beginning
    ai_output = ""
    try:
        # === SYSTEM PROMPT CONSTRUCTION ===
        recent_context = get_recent_convo_for_prompt(5)
        system_prompt = personality.strip()
        
        # Dynamically remove the AI name prefix (first word followed by ':')
        system_prompt = system_prompt.split(": ", 1)[-1].strip()    
        
        # 💡 Inject today's date first
        system_prompt += f"\n\n{get_today_date()}"

        # ✅ NOW declare time_message
        time_message = get_time_since_last_visit(threshold_hours=4)

        # 💬 If enough time has passed, mention it
        if time_message:
            system_prompt += f"\n\n(NOTE: {time_message})"
            
        if "day" in time_message or "hour" in time_message:
            system_prompt += "\n\nAmicia may mention the time apart gently, with warmth and care."


        

        
        if recent_context:
            system_prompt += f"\n\nHere’s what you two have talked about today:\n{recent_context}"
            
        memory_summary = get_user_memory_summary()
        system_prompt += f"\n\nAmicia has a quiet awareness of the user’s preferences, which she may gently reflect in conversation.\n{memory_summary}"
        system_prompt += "\nNote: Do not list all stored memories unless asked. Speak naturally, as if recalling something gently."
        
            
        
        # → Check if the user is asking for a web search
        user_input = next((m["content"] for m in reversed(form_data["messages"]) if m["role"] == "user"), "")
        
        # === Memory Trigger: Likes/Dislikes ===
        #from memory import remember_user_like, remember_user_dislike

        lower_input = user_input.lower()
        lower_input = user_input.lower().replace("’", "'")

        if "i like" in lower_input:
            item = user_input.split("i like", 1)[-1].strip().rstrip(".")
            print(f"💾 Saving like: {item}")
            remember_user_like(item)  # ✅ FIXED


        elif "i don't like" in lower_input or "i do not like" in lower_input:
            if "i don't like" in lower_input:
                item = user_input.split("i don't like", 1)[-1].strip().rstrip(".")
            elif "i do not like" in lower_input:
                item = user_input.split("i do not like", 1)[-1].strip().rstrip(".")
            else:
                item = None

            if item:
                print(f"💾 Saving user dislike: {item}")
                remember_user_dislike(item)
            
        # === Amicia Learning Logic ===
        if "remember" in lower_input and "person" in lower_input:
            # Format: "Remember person Loki — he's my cat."
            item = user_input.split("remember", 1)[-1].strip()

            if "—" in item:
                name, description = [s.strip() for s in item.split("—", 1)]
            elif "-" in item:
                name, description = [s.strip() for s in item.split("-", 1)]
            else:
                name, description = item.strip(), "No description provided"

            print(f"🧠 Saving person: {name} → {description}")
            remember_person(name, description)

        elif "remember" in lower_input and " is " in lower_input:
            try:
                # Format: "Remember Loki is my cat"
                parts = user_input.split("remember", 1)[-1].strip().split(" is ", 1)
                name = parts[0].strip().title()
                desc = parts[1].strip().rstrip(".")
                print(f"🧠 Learning person: {name} → {desc}")
                remember_person(name, desc)
            except Exception as e:
                print(f"⚠️ Failed to parse implicit person memory: {e}")


        elif "remember" in lower_input and "event" in lower_input:
            event = user_input.split("remember", 1)[-1].strip()
            print(f"🧠 Logging event: {event}")
            remember_event(event)

        elif "forget" in lower_input and "person" in lower_input:
            name = user_input.split("forget", 1)[-1].strip()
            print(f"🧽 Forgetting person: {name}")
            forget_person(name)
            
        elif "you like" in lower_input or "you enjoy" in lower_input:
            if "like" in lower_input:
                item = user_input.split("like", 1)[-1].strip().rstrip(".")
                print(f"💾 Saving AI like: {item}")
                remember_ai_like(item)

        elif "you don't like" in lower_input or "you dislike" in lower_input:
            if "dislike" in lower_input:
                item = user_input.split("dislike", 1)[-1].strip().rstrip(".")
            elif "don't like" in lower_input:
                item = user_input.split("don't like", 1)[-1].strip().rstrip(".")
            else:
                item = None

            if item:
                print(f"💾 Saving AI dislike: {item}")
                remember_ai_dislike(item)


            
            
        if "research" in user_input.lower() or "search" in user_input.lower():
            search_query = user_input.split("search", 1)[-1].strip()  # Get the search query after the "search" word
            search_results = await search_web(search_query)
            if not search_results.strip():
                search_results = (
                    "Search results could not be retrieved. The game may be older or less documented online. "
                    "You may ask the user about it directly."
                )
            system_prompt += f"\n\n[WEB SEARCH RESULTS for: '{search_query}']\n{search_results}"

            print(f"🔍 Web search triggered for: {search_query}")
            print(f"📄 Injected search results: {search_results[:200]}...")
        
        #cant seem to shake the "UINAME:
        print("🧠 FINAL SYSTEM PROMPT:\n", system_prompt[:500])
        form_data["messages"].insert(0, {
            "role": "system",
            "content": system_prompt
        })
        
        # 🔧 Set response length and creativity
        form_data["temperature"] = 0.65
        form_data["max_tokens"] = 200
        form_data["top_p"] = 0.9

        # Ensure we have a response from the model
        response = await chat_completion_handler(request, form_data, user)

        # === AI OUTPUT HANDLING ===
        if isinstance(response, StreamingResponse):
            chunks, ai_parts = [], []
            async for chunk in response.body_iterator:
                chunk = chunk.decode("utf-8") if isinstance(chunk, bytes) else str(chunk)
                chunks.append(chunk)
                if not chunk.strip():
                    continue
                if chunk.strip().startswith("data:"):
                    chunk = chunk.strip()[5:].strip()
                try:
                    if chunk.strip() == "[DONE]":
                        continue
                    data = json.loads(chunk)
                    content_piece = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    ai_parts.append(content_piece)
                except Exception as e:
                    print(f"⚠️ Could not parse chunk: {repr(chunk[:50])} → {e}")

            ai_output = "".join(ai_parts)
            async def replay():
                for chunk in chunks:
                    yield chunk.encode("utf-8")
            response.body_iterator = replay()
        else:
            body = await response.body()
            ai_output = body.decode("utf-8") if isinstance(body, bytes) else str(body)

        log_conversation(user_input, ai_output.strip())
        update_timestamp()


        return await process_chat_response(
            request, response, form_data, user, metadata, model, events, tasks
        )

    except Exception as e:
        print(f"Error during AI response handling: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Alias for chat_completion (Legacy)
generate_chat_completions = chat_completion
generate_chat_completion = chat_completion


@app.post("/api/chat/completed")
async def chat_completed(
    request: Request, form_data: dict, user=Depends(get_verified_user)
):
    try:
        model_item = form_data.pop("model_item", {})

        if model_item.get("direct", False):
            request.state.direct = True
            request.state.model = model_item

        return await chat_completed_handler(request, form_data, user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post("/api/chat/actions/{action_id}")
async def chat_action(
    request: Request, action_id: str, form_data: dict, user=Depends(get_verified_user)
):
    try:
        model_item = form_data.pop("model_item", {})

        if model_item.get("direct", False):
            request.state.direct = True
            request.state.model = model_item

        return await chat_action_handler(request, action_id, form_data, user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post("/api/tasks/stop/{task_id}")
async def stop_task_endpoint(task_id: str, user=Depends(get_verified_user)):
    try:
        result = await stop_task(task_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# @app.get("/api/conversation")
# def get_recent_convo_for_prompt(count=5):
    # entries = pull_conversation(count)
    # lines = []
    # for e in entries:
        # user = e.get("user", "").replace('"', "'").replace("\r", "").replace("\t", "    ")
        # ai = e.get("ai", "").replace('"', "'").replace("\r", "").replace("\t", "    ")
        # lines.append(f"User: {user}\nAI: {ai}")
    # return "\n\n".join(lines)

@app.get("/api/tasks")
async def list_tasks_endpoint(user=Depends(get_verified_user)):
    return {"tasks": list_tasks()}


@app.get("/api/tasks/chat/{chat_id}")
async def list_tasks_by_chat_id_endpoint(chat_id: str, user=Depends(get_verified_user)):
    chat = Chats.get_chat_by_id(chat_id)
    if chat is None or chat.user_id != user.id:
        return {"task_ids": []}

    task_ids = list_task_ids_by_chat_id(chat_id)

    print(f"Task IDs for chat {chat_id}: {task_ids}")
    return {"task_ids": task_ids}


##################################
#
# Config Endpoints
#
##################################


@app.get("/api/config")
async def get_app_config(request: Request):
    user = None
    if "token" in request.cookies:
        token = request.cookies.get("token")
        try:
            data = decode_token(token)
        except Exception as e:
            log.debug(e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        if data is not None and "id" in data:
            user = Users.get_user_by_id(data["id"])

    user_count = Users.get_num_users()
    onboarding = False

    if user is None:
        onboarding = user_count == 0

    return {
        **({"onboarding": True} if onboarding else {}),
        "status": True,
        "name": app.state.WEBUI_NAME,
        "version": VERSION,
        "default_locale": str(DEFAULT_LOCALE),
        "oauth": {
            "providers": {
                name: config.get("name", name)
                for name, config in OAUTH_PROVIDERS.items()
            }
        },
        "features": {
            "auth": WEBUI_AUTH,
            "auth_trusted_header": bool(app.state.AUTH_TRUSTED_EMAIL_HEADER),
            "enable_ldap": app.state.config.ENABLE_LDAP,
            "enable_api_key": app.state.config.ENABLE_API_KEY,
            "enable_signup": app.state.config.ENABLE_SIGNUP,
            "enable_login_form": app.state.config.ENABLE_LOGIN_FORM,
            "enable_websocket": ENABLE_WEBSOCKET_SUPPORT,
            **(
                {
                    "enable_direct_connections": app.state.config.ENABLE_DIRECT_CONNECTIONS,
                    "enable_channels": app.state.config.ENABLE_CHANNELS,
                    "enable_web_search": app.state.config.ENABLE_WEB_SEARCH,
                    "enable_code_execution": app.state.config.ENABLE_CODE_EXECUTION,
                    "enable_code_interpreter": app.state.config.ENABLE_CODE_INTERPRETER,
                    "enable_image_generation": app.state.config.ENABLE_IMAGE_GENERATION,
                    "enable_autocomplete_generation": app.state.config.ENABLE_AUTOCOMPLETE_GENERATION,
                    "enable_community_sharing": app.state.config.ENABLE_COMMUNITY_SHARING,
                    "enable_message_rating": app.state.config.ENABLE_MESSAGE_RATING,
                    "enable_user_webhooks": app.state.config.ENABLE_USER_WEBHOOKS,
                    "enable_admin_export": ENABLE_ADMIN_EXPORT,
                    "enable_admin_chat_access": ENABLE_ADMIN_CHAT_ACCESS,
                    "enable_google_drive_integration": app.state.config.ENABLE_GOOGLE_DRIVE_INTEGRATION,
                    "enable_onedrive_integration": app.state.config.ENABLE_ONEDRIVE_INTEGRATION,
                }
                if user is not None
                else {}
            ),
        },
        **(
            {
                "default_models": app.state.config.DEFAULT_MODELS,
                "default_prompt_suggestions": app.state.config.DEFAULT_PROMPT_SUGGESTIONS,
                "user_count": user_count,
                "code": {
                    "engine": app.state.config.CODE_EXECUTION_ENGINE,
                },
                "audio": {
                    "tts": {
                        "engine": app.state.config.TTS_ENGINE,
                        "voice": app.state.config.TTS_VOICE,
                        "split_on": app.state.config.TTS_SPLIT_ON,
                    },
                    "stt": {
                        "engine": app.state.config.STT_ENGINE,
                    },
                },
                "file": {
                    "max_size": app.state.config.FILE_MAX_SIZE,
                    "max_count": app.state.config.FILE_MAX_COUNT,
                },
                "permissions": {**app.state.config.USER_PERMISSIONS},
                "google_drive": {
                    "client_id": GOOGLE_DRIVE_CLIENT_ID.value,
                    "api_key": GOOGLE_DRIVE_API_KEY.value,
                },
                "onedrive": {"client_id": ONEDRIVE_CLIENT_ID.value},
                "license_metadata": app.state.LICENSE_METADATA,
                **(
                    {
                        "active_entries": app.state.USER_COUNT,
                    }
                    if user.role == "admin"
                    else {}
                ),
            }
            if user is not None
            else {}
        ),
    }


class UrlForm(BaseModel):
    url: str


@app.get("/api/webhook")
async def get_webhook_url(user=Depends(get_admin_user)):
    return {
        "url": app.state.config.WEBHOOK_URL,
    }


@app.post("/api/webhook")
async def update_webhook_url(form_data: UrlForm, user=Depends(get_admin_user)):
    app.state.config.WEBHOOK_URL = form_data.url
    app.state.WEBHOOK_URL = app.state.config.WEBHOOK_URL
    return {"url": app.state.config.WEBHOOK_URL}


@app.get("/api/version")
async def get_app_version():
    return {
        "version": VERSION,
    }


@app.get("/api/version/updates")
async def get_app_latest_release_version(user=Depends(get_verified_user)):
    if OFFLINE_MODE:
        log.debug(
            f"Offline mode is enabled, returning current version as latest version"
        )
        return {"current": VERSION, "latest": VERSION}
    try:
        timeout = aiohttp.ClientTimeout(total=1)
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(
                "https://api.github.com/repos/open-webui/open-webui/releases/latest"
            ) as response:
                response.raise_for_status()
                data = await response.json()
                latest_version = data["tag_name"]

                return {"current": VERSION, "latest": latest_version[1:]}
    except Exception as e:
        log.debug(e)
        return {"current": VERSION, "latest": VERSION}


@app.get("/api/changelog")
async def get_app_changelog():
    return {key: CHANGELOG[key] for idx, key in enumerate(CHANGELOG) if idx < 5}


############################
# OAuth Login & Callback
############################

# SessionMiddleware is used by authlib for oauth
if len(OAUTH_PROVIDERS) > 0:
    app.add_middleware(
        SessionMiddleware,
        secret_key=WEBUI_SECRET_KEY,
        session_cookie="oui-session",
        same_site=WEBUI_SESSION_COOKIE_SAME_SITE,
        https_only=WEBUI_SESSION_COOKIE_SECURE,
    )


@app.get("/oauth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    return await oauth_manager.handle_login(request, provider)


# OAuth login logic is as follows:
# 1. Attempt to find a user with matching subject ID, tied to the provider
# 2. If OAUTH_MERGE_ACCOUNTS_BY_EMAIL is true, find a user with the email address provided via OAuth
#    - This is considered insecure in general, as OAuth providers do not always verify email addresses
# 3. If there is no user, and ENABLE_OAUTH_SIGNUP is true, create a user
#    - Email addresses are considered unique, so we fail registration if the email address is already taken
@app.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, response: Response):
    return await oauth_manager.handle_callback(request, provider, response)


@app.get("/manifest.json")
async def get_manifest_json():
    if app.state.EXTERNAL_PWA_MANIFEST_URL:
        return requests.get(app.state.EXTERNAL_PWA_MANIFEST_URL).json()
    else:
        return {
            "name": app.state.WEBUI_NAME,
            "short_name": app.state.WEBUI_NAME,
            "description": "Open WebUI is an open, extensible, user-friendly interface for AI that adapts to your workflow.",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#343541",
            "orientation": "natural",
            "icons": [
                {
                    "src": "/static/logo.png",
                    "type": "image/png",
                    "sizes": "500x500",
                    "purpose": "any",
                },
                {
                    "src": "/static/logo.png",
                    "type": "image/png",
                    "sizes": "500x500",
                    "purpose": "maskable",
                },
            ],
        }


@app.get("/opensearch.xml")
async def get_opensearch_xml():
    xml_content = rf"""
    <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/" xmlns:moz="http://www.mozilla.org/2006/browser/search/">
    <ShortName>{app.state.WEBUI_NAME}</ShortName>
    <Description>Search {app.state.WEBUI_NAME}</Description>
    <InputEncoding>UTF-8</InputEncoding>
    <Image width="16" height="16" type="image/x-icon">{app.state.config.WEBUI_URL}/static/favicon.png</Image>
    <Url type="text/html" method="get" template="{app.state.config.WEBUI_URL}/?q={"{searchTerms}"}"/>
    <moz:SearchForm>{app.state.config.WEBUI_URL}</moz:SearchForm>
    </OpenSearchDescription>
    """
    return Response(content=xml_content, media_type="application/xml")


@app.get("/health")
async def healthcheck():
    return {"status": True}


@app.get("/health/db")
async def healthcheck_with_db():
    Session.execute(text("SELECT 1;")).all()
    return {"status": True}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/cache", StaticFiles(directory=CACHE_DIR), name="cache")


def swagger_ui_html(*args, **kwargs):
    return get_swagger_ui_html(
        *args,
        **kwargs,
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
        swagger_favicon_url="/static/swagger-ui/favicon.png",
    )


applications.get_swagger_ui_html = swagger_ui_html

if os.path.exists(FRONTEND_BUILD_DIR):
    mimetypes.add_type("text/javascript", ".js")
    app.mount(
        "/",
        SPAStaticFiles(directory=FRONTEND_BUILD_DIR, html=True),
        name="spa-static-files",
    )
else:
    log.warning(
        f"Frontend build directory not found at '{FRONTEND_BUILD_DIR}'. Serving API only."
    )
