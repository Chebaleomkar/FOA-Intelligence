# GSoC 2026 Proposal
# Title: ISSR AI-Powered Funding Intelligence

---

## 📌 Personal Information

| Field | Details |
|-------|---------|
| **Name** | Omkar Chebale |
| **Email** | omkarchebale0@gmail.com |
| **GitHub** | https://github.com/Chebaleomkar |
| **Project Repo** | https://github.com/Chebaleomkar/FOA-Intelligence |
| **Live Demo** | https://foa-dashboard.onrender.com/ |
| **Live API** | https://foa-api.onrender.com/docs |
| **Organization** | HumanAI Foundation / ISSR, University of Alabama |
| **Project Title** | AI-Powered Funding Intelligence (FOA Ingestion + Semantic Tagging) |

---

## 1. Synopsis

Funding Opportunity Announcements (FOAs) are distributed across dozens of federal agencies, vary widely in structure, and require significant manual effort to find and interpret. Research development teams at universities regularly lose time and opportunities because of this fragmentation.

This project proposes building an **open-source, AI-powered pipeline** that automatically:
1. Ingests FOAs from multiple public sources (Grants.gov, NSF) via official REST APIs
2. Extracts structured fields into a standardized, validated schema
3. Applies ontology-based semantic tags using a hybrid NLP approach
4. Exports clean, reproducible JSON/CSV outputs for downstream grant-matching systems

A working implementation has already been built and deployed as part of the screening task, demonstrating the feasibility of the full approach within the GSoC timeline.

---

## 2. Why This Problem Matters

University research development offices face a data fragmentation crisis:
- **144+ open opportunities** on Grants.gov for "artificial intelligence" alone at any time
- FOAs are spread across Grants.gov, NSF, NIH, DOE, and dozens of agency-specific portals
- Each source uses a different format, terminology, and schema
- A research coordinator may spend **hours per week** manually reviewing opportunities

Automating FOA ingestion and semantic tagging means:
- Investigators get matched to relevant opportunities faster
- Institutional strategy becomes data-driven
- The pipeline output feeds directly into a **grant-matching system** (the stated long-term goal)

---

## 3. Proposed Solution & Technical Approach

### 3.1 System Architecture

The pipeline has four modular stages:

```
Public APIs / URLs
       ↓
[Source-Aware Ingestion]   ← Grants.gov API + NSF Awards API
       ↓
[Structured Extraction]    ← Pydantic schema validation
       ↓
[Semantic Tagging Engine]  ← Rule-based + Embedding similarity (+ LLM stretch)
       ↓
[Export & Storage]         ← JSON / CSV / FAISS vector index
```

All stages are decoupled behind clean interfaces, making it easy to add new sources (NIH, DOE, SBIR) or tagging strategies without touching the core pipeline.

### 3.2 Data Sources

| Source | Method | Fields Available |
|--------|--------|-----------------|
| **Grants.gov** | REST API (search2 + fetchOpportunity) | Title, Agency, Dates, Description, Award Range |
| **NSF Awards** | REST API (awards.json) | Title, Agency, PI, Abstract, Program |
| **NIH (stretch)** | Reporter API or scrape | Project title, PA Number, Abstract |

> **No authentication is required** for any primary source.

### 3.3 FOA Schema (Standardized)

Every FOA, regardless of source, is normalized into:

```python
class FOARecord(BaseModel):
    foa_id: str          # Source ID or generated UUID
    title: str
    agency: str
    open_date: date      # ISO 8601
    close_date: date     # ISO 8601
    eligibility: str
    program_description: str
    award_range_min: float
    award_range_max: float
    source_url: str
    source: str          # "grants_gov" | "nsf"
    semantic_tags: List[SemanticTag]
    ingested_at: datetime
```

### 3.4 Semantic Tagging (Core NLP Work)

Three-layer tagging strategy:

#### Layer 1: Rule-Based Tagger (Always-On)
- Keyword / synonym matching against a **controlled ontology** (YAML)
- Title-boost scoring (title matches weighted 2x)
- Fast, deterministic, interpretable — zero external dependencies
- 31 tags across 4 categories already defined and working

#### Layer 2: Embedding Similarity Tagger (Core ML)
- Uses `sentence-transformers` (`all-MiniLM-L6-v2`)
- Pre-computes embeddings for all ontology tag descriptions
- At tag time: cosine similarity between FOA text and tag embeddings
- Handles synonymy and paraphrase that rule-based misses

#### Layer 3: LLM-Assisted Classification (Stretch Goal)
- Uses a free LLM (Groq LLaMA 3) for borderline cases
- Prompt: given FOA text, classify into ontology categories
- Ensemble with layers 1 & 2 for final confidence score

#### Controlled Ontology (4 categories, 31+ tags)
```yaml
research_domains: AI, biomedical, environmental science, engineering, social science...
methods: computational modeling, experimental, survey, mixed methods...
populations: youth, veterans, underserved communities, rural, indigenous...
sponsor_themes: innovation, equity & inclusion, national security, workforce dev...
```

### 3.5 Evaluation Methodology

To validate tagging consistency (required deliverable):
- Hand-label **50 FOAs** across diverse agencies as gold standard
- Compute per-tag **precision, recall, and F1**
- Compute **Cohen's Kappa** for inter-rater agreement (if 2+ annotators)
- Compare rule-based vs. embedding vs. ensemble performance
- Target: F1 > 0.75 on top 10 most common tags

---

## 4. Deliverables

By the end of the project period:

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | ✅ Working FOA ingestion pipeline (Grants.gov + NSF) | Started |
| 2 | ✅ Standardized JSON + CSV FOA dataset | Done |
| 3 | ✅ Rule-based semantic tagging module | Done |
| 4 | 🔧 Embedding-based semantic tagging module | Scaffolded |
| 5 | 🔧 Evaluation dataset (50 FOAs) + precision/recall metrics | Planned |
| 6 | 🔧 Documentation and reproducibility guide | In Progress |
| 7 | ⭐ LLM-assisted classification (stretch) | Planned |
| 8 | ⭐ FAISS vector index for similarity search (stretch) | Planned |
| 9 | ⭐ NIH as a third source (stretch) | Planned |

---

## 5. Implementation Timeline

> GSoC 2026 runs approximately **May 29 – August 25** (12 weeks)

### Pre-GSoC (Now → May 28)
| Period | Task |
|--------|------|
| Feb–Mar | Refine embedding tagger, add unit tests |
| Mar 16–31 | Submit formal proposal via GSoC portal |
| Apr | Community bonding, sync with mentors, finalize scope |

### GSoC Period
| Week | Phase | Goal | Milestone |
|------|-------|------|-----------|
| **1** | Kickoff | Mentor sync, finalize schema, setup CI | Dev environment ready |
| **2–3** | Source Expansion | Complete Grants.gov + NSF, add NIH (stretch) | All source connectors stable |
| **4–5** | Extraction | Edge case handling, date/amount parsing, deduplication | Schema validation passing |
| **6–7** | Embedding Tagger | Integrate `all-MiniLM-L6-v2`, tune threshold, add caching | Embedding tagger live |
| **8** | Midterm Evaluation | Demo ingestion + rule + embedding pipeline | **Midterm milestone** |
| **9–10** | Evaluation | Hand-label 50 FOAs, compute F1/Kappa metrics | Evaluation report |
| **11** | Stretch Goals | FAISS search OR LLM layer | At least 1 stretch done |
| **12** | Documentation & Polish | Final README, reproducibility guide, demo video | **Final submission** |

---

## 6. About Me

I am a Python developer with hands-on experience building NLP pipelines, REST APIs, and AI-assisted systems.

**Relevant Skills:**
- Python (2+ years), including Pydantic, FastAPI, Streamlit
- NLP: Sentence-Transformers, Hugging Face, spaCy
- API integration: REST APIs, scraping with BeautifulSoup
- ML: Embeddings, cosine similarity, semantic search (Pinecone, FAISS)
- Data: JSON/CSV processing, Pandas
- DevOps: Git/GitHub, Docker, Render deployment

**Relevant Projects:**
- [FOA-Intelligence](https://github.com/Chebaleomkar/FOA-Intelligence) — This project (screening task + deployed system)
- [Blog Recommendation System] — Built a semantic similarity recommendation engine using Gemini embeddings and MongoDB
- [RAG Pipeline] — Implemented Retrieval-Augmented Generation with Pinecone vector store

**Time Commitment:** I am able to contribute **35+ hours/week** during the GSoC period.

---

## 7. Community Engagement

- Screening task submitted: February 20, 2026
- Materials reviewed by mentors: Confirmed
- Plan to submit proposals for **2 ISSR projects** as recommended

---

## 8. References

- [Project Description](https://humanai.foundation/gsoc/2026/proposal_ISSR4.html)
- [GSoC Guidelines](https://google.github.io/gsocguides/student/)
- [Grants.gov API Documentation](https://api.grants.gov)
- [NSF Awards API](https://api.nsf.gov/services/v1/awards.json)

---

*Last updated: 2026-02-21*
*Proposal must be submitted via the GSoC portal between March 16–31, 2026.*
*Named: ISSR AI-Powered Funding Intelligence*
