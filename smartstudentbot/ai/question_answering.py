from typing import Optional
from sentence_transformers import SentenceTransformer, util
import torch

from smartstudentbot.utils.json_utils import read_json_file
from smartstudentbot.utils.logger import logger

QNA_FILE_PATH = "smartstudentbot/qna.json"
KNOWLEDGE_FILE_PATH = "smartstudentbot/knowledge.json"
SIMILARITY_THRESHOLD = 0.8  # Confidence threshold for a match

# Load the model only once when the module is imported.
# This is a memory-intensive operation.
logger.info("Loading sentence-transformer model...")
try:
    model = SentenceTransformer('distilbert-base-multilingual-cased')
    logger.info("Sentence-transformer model loaded successfully.")
except Exception as e:
    logger.critical(f"Failed to load sentence-transformer model: {e}")
    model = None

# Pre-compute knowledge base embeddings if possible (or cache them)
# For simplicity, we'll re-compute each time for now, but caching is a key optimization.
knowledge_base = None
knowledge_embeddings = None

def _load_knowledge():
    """Loads the knowledge base and computes embeddings."""
    global knowledge_base, knowledge_embeddings
    if model is None:
        return

    knowledge_data = read_json_file(KNOWLEDGE_FILE_PATH)
    if not knowledge_data or "data" not in knowledge_data:
        logger.error(f"Invalid or empty data in {KNOWLEDGE_FILE_PATH}")
        knowledge_base = []
        return

    knowledge_base = knowledge_data["data"]
    questions = [item["q"] for item in knowledge_base]
    if not questions:
        logger.info("Knowledge base is empty.")
        knowledge_embeddings = None
        return

    logger.info(f"Computing embeddings for {len(questions)} knowledge base questions...")
    knowledge_embeddings = model.encode(questions, convert_to_tensor=True)
    logger.info("Embeddings computed.")

# Load knowledge base on startup
_load_knowledge()


async def get_simple_answer(question: str) -> Optional[str]:
    """Searches for a simple, case-insensitive, exact-match answer."""
    qna_data = read_json_file(QNA_FILE_PATH)
    if not qna_data or "data" not in qna_data:
        return None
    question_lower = question.strip().lower()
    for item in qna_data["data"]:
        if item["q"].strip().lower() == question_lower:
            return item.get("a")
    return None

async def get_semantic_answer(question: str) -> Optional[str]:
    """Searches for a semantically similar answer using sentence embeddings."""
    if model is None or knowledge_embeddings is None or not knowledge_base:
        logger.warning("Semantic search is unavailable (model or knowledge base not loaded).")
        return None

    logger.info(f"Performing semantic search for: '{question}'")
    question_embedding = model.encode(question, convert_to_tensor=True)

    # Compute cosine similarities
    cosine_scores = util.cos_sim(question_embedding, knowledge_embeddings)

    # Find the best match
    best_score_index = torch.argmax(cosine_scores)
    best_score = cosine_scores[0][best_score_index].item()

    logger.info(f"Best semantic match score: {best_score:.4f}")

    if best_score >= SIMILARITY_THRESHOLD:
        logger.info(f"Found semantic match with score {best_score:.4f}")
        return knowledge_base[best_score_index].get("a")

    logger.info("No semantic match found above threshold.")
    return None

async def get_answer(question: str) -> Optional[str]:
    """
    Orchestrates the search for an answer, trying simple match first, then semantic.
    """
    # 1. Try for a simple, direct match first for speed and accuracy.
    logger.info(f"Searching for answer to: '{question}'")
    simple_answer = await get_simple_answer(question)
    if simple_answer:
        logger.info("Found answer via simple match.")
        return simple_answer

    # 2. If no simple match, try semantic search.
    semantic_answer = await get_semantic_answer(question)
    if semantic_answer:
        logger.info("Found answer via semantic search.")
        return semantic_answer

    logger.info(f"Could not find any answer for: '{question}'")
    return None
