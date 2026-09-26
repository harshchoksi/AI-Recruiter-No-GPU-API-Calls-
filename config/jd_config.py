"""
Structured JD requirements extracted from the Redrob Senior AI Engineer job description.
This is the 'ground truth' of what the JD is asking for, parsed from the actual document.
"""


# ─── Required Skills (absolute must-haves from JD) ──────────────────────────
REQUIRED_SKILLS = {
    # Skill cluster → keywords that indicate this skill
    "embeddings_retrieval": {
        "keywords": [
            "embeddings", "embedding", "sentence-transformers", "sentence transformers",
            "openai embeddings", "bge", "e5", "retrieval", "dense retrieval",
            "semantic search", "vector search", "similarity search", "rag",
            "retrieval augmented", "information retrieval",
        ],
        "weight": 1.0,
        "description": "Production experience with embeddings-based retrieval systems",
    },
    "vector_databases": {
        "keywords": [
            "pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
            "elasticsearch", "vector database", "vector db", "vector store",
            "hybrid search", "ann", "approximate nearest",
        ],
        "weight": 1.0,
        "description": "Production experience with vector databases or hybrid search",
    },
    "python": {
        "keywords": [
            "python", "django", "flask", "fastapi", "pytorch", "tensorflow",
            "pyspark", "pandas", "numpy", "scikit-learn", "sklearn",
        ],
        "weight": 0.8,
        "description": "Strong Python skills",
    },
    "ranking_evaluation": {
        "keywords": [
            "ranking", "ndcg", "mrr", "map", "evaluation", "a/b test",
            "ab test", "learning to rank", "reranking", "re-ranking",
            "recommendation", "search ranking", "relevance",
        ],
        "weight": 1.0,
        "description": "Experience designing evaluation frameworks for ranking systems",
    },
    "ml_production": {
        "keywords": [
            "production", "deploy", "deployment", "mlops", "ml pipeline",
            "model serving", "inference", "monitoring", "ml system",
            "machine learning system", "real users", "scale",
        ],
        "weight": 0.9,
        "description": "Production ML system experience (not just research/notebooks)",
    },
}

# ─── Nice-to-Have Skills ────────────────────────────────────────────────────
NICE_TO_HAVE_SKILLS = {
    "llm_finetuning": {
        "keywords": [
            "fine-tuning", "finetuning", "fine tuning", "lora", "qlora", "peft",
            "rlhf", "instruction tuning", "llm training",
        ],
        "weight": 0.5,
        "description": "LLM fine-tuning experience",
    },
    "learning_to_rank": {
        "keywords": [
            "learning to rank", "xgboost", "lightgbm", "catboost", "gradient boosting",
            "neural ranking", "lambdamart",
        ],
        "weight": 0.5,
        "description": "Learning-to-rank models",
    },
    "distributed_systems": {
        "keywords": [
            "distributed", "kafka", "spark", "airflow", "kubernetes", "k8s",
            "docker", "microservices", "scalability", "high availability",
        ],
        "weight": 0.3,
        "description": "Background in distributed systems",
    },
    "open_source": {
        "keywords": [
            "open source", "open-source", "github", "contributor", "contribution",
            "maintainer",
        ],
        "weight": 0.3,
        "description": "Open-source contributions in AI/ML",
    },
    "nlp": {
        "keywords": [
            "nlp", "natural language processing", "text classification",
            "named entity", "ner", "transformer", "bert", "gpt",
            "language model", "tokenization", "text mining",
        ],
        "weight": 0.6,
        "description": "NLP expertise",
    },
}

# ─── Anti-Signals (things the JD explicitly does NOT want) ───────────────────
ANTI_SIGNALS = {
    "title_chaser": {
        "description": "Switching companies every 1.5 years for title bumps",
        "check": "avg_tenure < 18 months with title changes",
    },
    "framework_enthusiast": {
        "description": "Only LangChain/recent LLM wrapper experience without deep ML",
        "keywords": ["langchain", "llamaindex", "llama index"],
    },
    "consulting_only": {
        "description": "Entire career at consulting firms (TCS, Infosys, Wipro, etc.)",
        "check": "all companies in CONSULTING_COMPANIES",
    },
    "pure_research": {
        "description": "Only research, no production deployment",
        "check": "no production keywords in career descriptions",
    },
    "no_recent_code": {
        "description": "Hasn't written production code in 18+ months",
        "check": "recent roles are architecture/management only",
    },
    "cv_speech_only": {
        "description": "Primary expertise in computer vision/speech/robotics without NLP/IR",
        "keywords": ["computer vision", "image classification", "object detection",
                     "speech recognition", "robotics", "autonomous"],
    },
}

# ─── Career Description Keywords for Production AI Detection ─────────────────
PRODUCTION_AI_KEYWORDS = [
    "embeddings", "embedding", "retrieval", "ranking", "recommendation",
    "search", "vector", "similarity", "ml pipeline", "model serving",
    "inference", "deployed", "production", "real users", "a/b test",
    "monitoring", "latency", "throughput", "scale", "fine-tun",
    "training pipeline", "feature store", "mlops",
]

# ─── Seniority Level from JD ────────────────────────────────────────────────
JD_SENIORITY = {
    "level": "senior",
    "yoe_range": (5, 9),
    "flexibility": "Will consider 3-4 yrs with unusually high-impact work",
}

# ─── Cultural Signals from JD ───────────────────────────────────────────────
CULTURAL_SIGNALS = {
    "async_first": "Writes a lot, async communication",
    "scrappy": "Ship fast, iterate based on user feedback",
    "disagree_openly": "Direct communication style",
    "product_engineering": "Think about product, not just code",
    "startup_stage": "Series A, 4→12 engineers, things change fast",
}

# ─── Work Mode from JD ──────────────────────────────────────────────────────
JD_WORK_MODE = {
    "type": "hybrid",
    "locations": ["Pune", "Noida"],
    "flexibility": "Flexible cadence, quarterly offsites",
    "notice_preference": "Sub-30-day notice preferred",
}
