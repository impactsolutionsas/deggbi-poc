# DeggBi AI

## Identité du projet

**DeggBi AI** (« La Vérité » en wolof) est une plateforme de détection de deepfakes et de vérification de contenus multimédias, accessible via WhatsApp, ciblant l'Afrique francophone.

- **Repo** : https://github.com/impactsolutionsas/deggbi-poc
- **Hackathon** : iSAFE — Forum SMSI 2026 — Thème : Démasquer la Tromperie
- **Stack** : FastAPI + Celery + Supabase + Render + HuggingFace

---

## Architecture en un coup d'œil

```
WhatsApp / Telegram / Web
         ↓
   FastAPI (Render Web Service)
         ↓
   Content Router  →  détecte : texte / image / audio
         ↓                    ↓
   TruthScan              DeepShield
   NLP + OCR + Whisper    EfficientNet + Wav2Vec2
   AfroXLMR + RAG         FaceForensics++
         ↓                    ↓
         └──── Scoring Engine (0–100) ────┘
                       ↓
              Rapport multilingue
              FR / EN / Wolof
                       ↓
              Supabase (PostgreSQL + pgvector + Storage)
```

---

## Structure du projet

```
deggbi-poc/
├── app/
│   ├── main.py              # FastAPI app + routers
│   ├── config.py            # Settings (Supabase, HuggingFace, WhatsApp)
│   ├── api/
│   │   ├── whatsapp.py      # Webhook WhatsApp Business API
│   │   ├── telegram.py      # Webhook Telegram Bot
│   │   └── rest.py          # API REST B2B
│   ├── core/
│   │   ├── router.py        # Content Router (détecte le type de contenu)
│   │   └── scoring.py       # Scoring Engine — calcule le score final 0–100
│   ├── models/
│   │   ├── analysis.py      # Pydantic models — Analysis, Score, Report
│   │   └── database.py      # Supabase client + helpers
│   ├── services/
│   │   ├── truthscan.py     # Module TruthScan (NLP + OCR + STT + RAG)
│   │   ├── deepshield.py    # Module DeepShield (image + audio deepfake)
│   │   └── reporter.py      # Génération du rapport multilingue
│   ├── tasks/
│   │   └── analysis.py      # Celery tasks async
│   └── utils/
│       ├── whatsapp_client.py   # Envoi de messages WhatsApp
│       └── media.py             # Download + upload médias Supabase
├── frontend/                # Next.js 14 dashboard B2B
│   ├── src/app/
│   └── src/components/
├── tests/
├── scripts/
│   └── setup_supabase.sql   # Init schema PostgreSQL + pgvector
├── render.yaml              # Infrastructure as Code
├── requirements.txt
├── .env.example
├── Dockerfile
└── CLAUDE.md                # CE FICHIER
```

---

## Stack technique

| Couche | Techno | Rôle |
|--------|--------|------|
| API | FastAPI + Uvicorn | Web service principal |
| Queue | Celery + Redis (Upstash) | Tâches async IA |
| DB | Supabase PostgreSQL | Données + vecteurs RAG |
| Storage | Supabase Storage | Médias (images, audios) |
| Auth | Supabase Auth | API keys B2B |
| NLP | AfroXLMR + LLaMA 3 | Fact-checking multilingue |
| STT | Whisper Large-v3 | Transcription vocale |
| OCR | PaddleOCR | Texte dans images |
| Vision | EfficientNet-B4 | Deepfake image |
| Audio | Wav2Vec2 + RawNet2 | Deepfake audio/voix clonée |
| RAG | LangChain + pgvector | Base de connaissances vérifiées |
| Infra | Render.com | Déploiement Web + Worker |
| Frontend | Next.js 14 + Tailwind | Dashboard B2B |

---

## Variables d'environnement

Toutes les variables sont dans `.env` (non commité) — voir `.env.example`.

Variables critiques :
- `SUPABASE_URL` — URL du projet Supabase
- `SUPABASE_SERVICE_KEY` — clé service (admin, backend uniquement)
- `SUPABASE_ANON_KEY` — clé publique (frontend Next.js)
- `WHATSAPP_TOKEN` — Meta Business API token
- `WHATSAPP_PHONE_ID` — ID numéro WhatsApp Business
- `WHATSAPP_VERIFY_TOKEN` — token de vérification webhook
- `TELEGRAM_BOT_TOKEN` — BotFather token
- `REDIS_URL` — Upstash Redis URL
- `HUGGINGFACE_API_KEY` — HuggingFace Inference API
- `GOOGLE_FACTCHECK_KEY` — Google Fact Check Tools API
- `SECRET_KEY` — JWT signing key (générer avec `openssl rand -hex 32`)

---

## Score DeggBi — Logique de scoring

```python
# Score final = combinaison pondérée des deux modules
score_final = (score_truthscan * 0.5) + (score_deepshield * 0.5)

# Verdicts
0–30   → CONTENU FIABLE      (vert)
31–60  → CONTENU DOUTEUX     (orange)
61–85  → PROBABLEMENT FAUX   (rouge clair)
86–100 → DEEPFAKE CONFIRMÉ   (rouge vif)
```

---

## Règles de développement

### Toujours respecter

- **Async partout** : toutes les routes FastAPI sont `async def`
- **Celery pour l'IA** : les appels HuggingFace et les analyses lourdes passent par des tasks Celery, jamais directement dans le webhook
- **Réponse immédiate WhatsApp** : le webhook répond en < 5s (accusé de réception), puis envoie le rapport en second message
- **Supabase client** : utiliser `supabase-py` — jamais psycopg2 directement
- **Gestion d'erreurs** : chaque service IA a un fallback gracieux — si HuggingFace timeout, retourner score partiel avec mention "analyse incomplète"
- **Pydantic models** : tous les objets entrants/sortants sont typés avec Pydantic v2
- **Tests** : chaque nouveau service a un test unitaire dans `/tests/`

### Conventions de nommage

- Fichiers : `snake_case.py`
- Classes : `PascalCase`
- Variables / fonctions : `snake_case`
- Constants : `UPPER_SNAKE_CASE`
- Routes API : `/api/v1/...`

### Format du rapport WhatsApp (sortie)

```
🔍 *Analyse DeggBi AI*

Verdict : ⚠️ DEEPFAKE CONFIRMÉ
Score : 94/100

📊 Détails :
• Voix synthétique détectée (Wav2Vec2)
• Aucune source officielle correspondante
• Confiance : 96.2%

⏱ Analysé en 18 secondes

➡️ Ne pas partager — Signaler aux autorités
```

---

## Scénarios de démo (Hackathon)

### Scénario 1 — Faux discours présidentiel
- Input : audio WhatsApp (voix clonée)
- Pipeline : Whisper → Wav2Vec2 → Fact-check
- Output attendu : Score 94/100 — DEEPFAKE CONFIRMÉ

### Scénario 2 — Photo virale recyclée
- Input : image WhatsApp (inondation Bangladesh présentée comme Sénégal)
- Pipeline : EfficientNet → Reverse search → OCR
- Output attendu : Score 78/100 — PROBABLEMENT FAUX

### Scénario 3 — Arnaque Mobile Money
- Input : texte SMS (faux Orange Money)
- Pipeline : NLP → URL analysis → Pattern matching
- Output attendu : Score 88/100 — ARNAQUE CONFIRMÉE

---

## Commandes utiles

```bash
# Dev local
uvicorn app.main:app --reload --port 8000

# Worker Celery
celery -A app.tasks worker --loglevel=info --concurrency=2

# Tests
pytest tests/ -v

# Migrations Supabase (via psql ou Supabase Studio)
psql $DATABASE_URL -f scripts/setup_supabase.sql

# Deploy (auto via GitHub → Render)
git push origin main
```

---

## État d'avancement

- [ ] Setup Supabase (schema + pgvector)
- [ ] FastAPI app skeleton
- [ ] Webhook WhatsApp
- [ ] Content Router
- [ ] TruthScan (NLP + OCR + Whisper)
- [ ] DeepShield (EfficientNet + Wav2Vec2)
- [ ] Scoring Engine
- [ ] Rapport multilingue
- [ ] Dashboard Next.js
- [ ] Démo 3 scénarios
