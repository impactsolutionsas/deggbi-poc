"""
RAG Pipeline — Recherche sémantique dans la base de connaissances vérifiées (pgvector).
Utilise sentence-transformers pour les embeddings et Supabase pgvector pour le stockage/recherche.
"""
import httpx
import structlog
from app.config import settings
from app.models.database import get_supabase

logger = structlog.get_logger()

HF_API_URL = "https://router.huggingface.co/hf-inference/models"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384  # MiniLM dimension (compatible avec vector(768) via padding)
TOP_K = 5
SIMILARITY_THRESHOLD = 0.65


async def generate_embedding(text: str) -> list[float] | None:
    """Génère un embedding via HuggingFace Inference API."""
    if not settings.huggingface_api_key:
        return None
    try:
        url = f"{HF_API_URL}/{EMBEDDING_MODEL}"
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json={"inputs": text[:512]},
                headers=headers,
            )
            result = resp.json()

        if isinstance(result, list) and len(result) > 0:
            embedding = result if isinstance(result[0], float) else result[0]
            # Pad to 768 dims si nécessaire (colonne vector(768))
            if len(embedding) < 768:
                embedding = embedding + [0.0] * (768 - len(embedding))
            return embedding[:768]
        return None
    except Exception as e:
        logger.warning("Embedding generation failed", error=str(e))
        return None


async def search_knowledge_base(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Recherche sémantique dans la table embeddings via pgvector.
    Retourne les documents les plus similaires.
    """
    embedding = await generate_embedding(query)
    if not embedding:
        return []

    try:
        sb = get_supabase()
        response = sb.rpc(
            "match_embeddings",
            {
                "query_embedding": embedding,
                "match_threshold": SIMILARITY_THRESHOLD,
                "match_count": top_k,
            },
        ).execute()
        return response.data or []
    except Exception as e:
        logger.warning("RAG search failed", error=str(e))
        return []


async def add_to_knowledge_base(
    content: str,
    source_url: str | None = None,
    language: str = "fr",
) -> bool:
    """Ajoute un document vérifié à la base de connaissances."""
    embedding = await generate_embedding(content)
    if not embedding:
        return False

    try:
        sb = get_supabase()
        sb.table("embeddings").insert({
            "content": content,
            "source_url": source_url,
            "language": language,
            "embedding": embedding,
        }).execute()
        logger.info("Document ajouté à la base RAG", source=source_url)
        return True
    except Exception as e:
        logger.error("RAG insert failed", error=str(e))
        return False


async def rag_fact_check(claim: str) -> dict:
    """
    Vérifie une affirmation contre la base de connaissances.
    Retourne un score de confiance et les sources trouvées.
    """
    results = await search_knowledge_base(claim)

    if not results:
        return {
            "score": None,
            "sources": [],
            "matched": False,
            "details": "Aucune correspondance dans la base de connaissances",
        }

    sources = []
    for r in results:
        sources.append({
            "content": r.get("content", "")[:150],
            "source_url": r.get("source_url"),
            "similarity": r.get("similarity", 0),
        })

    avg_similarity = sum(r.get("similarity", 0) for r in results) / len(results)

    # Plus la similarité est haute avec des faits vérifiés, plus le contenu est fiable
    # Score inversé : haute similarité = bas score de désinformation
    rag_score = max(0, 100 - (avg_similarity * 100))

    return {
        "score": round(rag_score, 1),
        "sources": [s["source_url"] for s in sources if s["source_url"]],
        "matched": True,
        "details": f"RAG: {len(results)} sources trouvées (similarité moy. {avg_similarity:.2f})",
    }
