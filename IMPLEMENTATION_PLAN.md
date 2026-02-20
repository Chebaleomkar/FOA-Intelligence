# 🚀 FOA-Intelligence: Implementation Plan & GSoC Preparation Guide

## 📋 Table of Contents
1. [Project Overview & Analysis](#1-project-overview--analysis)
2. [Architecture Design](#2-architecture-design)
3. [Phase-wise Implementation Plan](#3-phase-wise-implementation-plan)
4. [Screening Task Strategy](#4-screening-task-strategy)
5. [Technical Deep Dives](#5-technical-deep-dives)
6. [GSoC Proposal Tips](#6-gsoc-proposal-tips)
7. [Timeline & Milestones](#7-timeline--milestones)

---

## 1. Project Overview & Analysis

### What This Project Is
You're building an **open-source pipeline** that:
1. **Ingests** Funding Opportunity Announcements (FOAs) from public APIs (Grants.gov, NSF)
2. **Extracts** structured fields (title, agency, dates, eligibility, etc.)
3. **Tags** them semantically using NLP (rule-based + embeddings + optional LLM)
4. **Exports** clean JSON + CSV outputs for downstream grant matching

### Why This Project is a Good Fit for You
- It's a **data engineering + NLP pipeline** — very practical and impressive
- Uses Python, web scraping, embeddings, and structured data — skills you already have
- **Intermediate difficulty** — achievable in GSoC timeline with stretch goals for ambition
- Clear deliverables — mentors can evaluate progress objectively

### Key Insight: Use APIs, Not Scraping!
**Critical discovery**: Both Grants.gov and NSF provide **free, public REST APIs** with **no authentication required** for searching and fetching funding opportunities. This is far more reliable than HTML scraping.

| Source | API Endpoint | Auth Required? | Data Format |
|--------|-------------|----------------|-------------|
| **Grants.gov** | `https://api.grants.gov/v1/api/search2` | ❌ No | JSON |
| **Grants.gov** | `https://api.grants.gov/v1/api/fetchOpportunity` | ❌ No | JSON |
| **NSF Awards** | `https://api.nsf.gov/services/v1/awards.json` | ❌ No | JSON/XML |

> **Strategy**: Use APIs as primary ingestion method, fall back to HTML/PDF scraping only when API data is incomplete (e.g., full program descriptions in PDFs).

---

## 2. Architecture Design

### High-Level Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FOA Intelligence Pipeline                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │   INGESTION   │───▶│  EXTRACTION  │───▶│  SEMANTIC TAGGING     │  │
│  │              │    │              │    │                       │  │
│  │ • Grants.gov │    │ • Field      │    │ • Rule-based tags     │  │
│  │   API        │    │   Extraction │    │ • Embedding similarity│  │
│  │ • NSF API    │    │ • Date       │    │ • LLM classification  │  │
│  │ • PDF Parser │    │   Parsing    │    │   (stretch goal)      │  │
│  │ • HTML Parse │    │ • Schema     │    │ • Ontology alignment  │  │
│  │              │    │   Validation │    │                       │  │
│  └──────────────┘    └──────────────┘    └───────────┬───────────┘  │
│                                                      │              │
│                                          ┌───────────▼───────────┐  │
│                                          │    STORAGE & EXPORT   │  │
│                                          │                       │  │
│                                          │ • JSON export         │  │
│                                          │ • CSV export          │  │
│                                          │ • Update workflow     │  │
│                                          │ • FAISS index (opt.)  │  │
│                                          └───────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
FOA-Intelligence/
├── main.py                      # CLI entry point
├── requirements.txt             # Dependencies
├── README.md                    # Documentation
├── config/
│   ├── settings.py              # Configuration settings
│   └── ontology.yaml            # Controlled vocabulary/ontology
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract ingestion interface
│   │   ├── grants_gov.py        # Grants.gov API ingestion
│   │   ├── nsf.py               # NSF API ingestion
│   │   └── pdf_parser.py        # PDF text extraction
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── field_extractor.py   # Structured field extraction
│   │   ├── schema.py            # FOA schema (Pydantic model)
│   │   └── normalizer.py        # Text/date normalization
│   ├── tagging/
│   │   ├── __init__.py
│   │   ├── rule_based.py        # Keyword/regex rule-based tagger
│   │   ├── embedding_tagger.py  # Sentence-transformer similarity tagger
│   │   ├── llm_tagger.py        # Optional LLM-based tagger (stretch)
│   │   └── ontology.py          # Ontology loader + tag definitions
│   ├── export/
│   │   ├── __init__.py
│   │   ├── json_exporter.py     # JSON output
│   │   └── csv_exporter.py      # CSV output
│   └── evaluation/
│       ├── __init__.py
│       ├── evaluator.py         # Precision/recall/agreement metrics
│       └── gold_standard.json   # Hand-labeled evaluation set
├── tests/
│   ├── test_ingestion.py
│   ├── test_extraction.py
│   ├── test_tagging.py
│   └── test_export.py
├── out/                         # Default output directory
│   ├── foa.json
│   └── foa.csv
├── data/                        # Raw/cached data (gitignored)
│   └── cache/
└── docs/
    ├── DESIGN.md                # Design decisions
    ├── ONTOLOGY.md              # Ontology documentation
    └── EVALUATION.md            # Evaluation methodology + results
```

---

## 3. Phase-wise Implementation Plan

### Phase 0: Foundation Setup (Week 0 — Pre-GSoC) ⬅️ DO THIS NOW
> **Goal**: Set up project skeleton + complete the screening task

- [x] Read project description
- [ ] Set up Python project with virtual environment
- [ ] Create project directory structure
- [ ] Initialize git repository
- [ ] Define FOA schema (Pydantic model)
- [ ] **Complete screening task** (see Section 4)
- [ ] Write initial README.md
- [ ] Submit screening task + CV

### Phase 1: FOA Ingestion (GSoC Weeks 1–3)
> **Goal**: Build robust ingestion from 2+ public sources

#### Grants.gov Ingestion
- Implement API client for `search2` and `fetchOpportunity`
- Handle pagination (API returns paginated results)
- Cache raw API responses to `data/cache/`
- Rate limiting and error handling

#### NSF Ingestion
- Implement NSF Awards API client
- Query by program, date range, keywords
- Map NSF-specific fields to unified schema

#### PDF/HTML Fallback
- Use `PyPDF2`/`pdfminer` for PDF extraction when linked in API responses
- Use `BeautifulSoup` for any supplementary HTML pages
- Text cleaning and normalization

### Phase 2: Structured Extraction + Normalization (GSoC Weeks 3–5)
> **Goal**: Extract all required fields into a standardized schema

#### Schema Definition (Pydantic)
```python
class FOARecord(BaseModel):
    foa_id: str                    # Generated UUID if missing
    title: str
    agency: str
    open_date: Optional[date]      # ISO format
    close_date: Optional[date]     # ISO format
    eligibility: Optional[str]
    program_description: Optional[str]
    award_range_min: Optional[float]
    award_range_max: Optional[float]
    source_url: str
    source: str                    # "grants_gov" | "nsf"
    raw_text: Optional[str]        # Original text for tagging
    semantic_tags: List[SemanticTag] = []
    ingested_at: datetime
```

#### Normalization
- Date parsing: Handle multiple formats → ISO 8601
- Agency name normalization (e.g., "NSF" vs "National Science Foundation")
- Currency/amount extraction from free text
- Text cleaning: Remove HTML entities, normalize whitespace

### Phase 3: Semantic Tagging (GSoC Weeks 5–8) ⭐ CORE ML WORK
> **Goal**: Tag FOAs with research domains, methods, populations, sponsor themes

#### 3a. Controlled Ontology Design
Create `config/ontology.yaml` with hierarchical tags:

```yaml
research_domains:
  - artificial_intelligence:
      synonyms: [AI, machine learning, deep learning, neural networks]
      children: [nlp, computer_vision, reinforcement_learning]
  - biomedical:
      synonyms: [health, medical, clinical, pharmaceutical]
      children: [genomics, epidemiology, mental_health]
  - environmental_science:
      synonyms: [climate, ecology, sustainability, earth science]
  - social_science:
      synonyms: [sociology, psychology, anthropology, economics]
  # ... more domains

methods:
  - computational_modeling
  - survey_research
  - field_study
  - experimental
  - mixed_methods

populations:
  - underserved_communities
  - veterans
  - youth
  - elderly
  - indigenous

sponsor_themes:
  - innovation
  - workforce_development
  - national_security
  - equity_and_inclusion
  - infrastructure
```

#### 3b. Rule-Based Tagger
- **Keyword matching**: Match ontology terms + synonyms against FOA text
- **Regex patterns**: Extract structured patterns (e.g., "ages 18–65")
- **Confidence scoring**: Based on term frequency and position

#### 3c. Embedding Similarity Tagger
- Use `sentence-transformers` (e.g., `all-MiniLM-L6-v2`) 
- Encode ontology tag descriptions as reference embeddings
- Encode FOA text (title + description) as query embeddings
- Compute cosine similarity → assign tags above threshold
- This is the **key NLP differentiator** of the project

#### 3d. LLM-Assisted Classification (Stretch Goal)
- Use a free/cheap LLM API (Groq, Ollama, etc.)
- Prompt: "Given this FOA, classify into these ontology categories..."
- Use LLM as a third signal, ensemble with rule-based + embedding

#### Tag Fusion Strategy
```
Final Tags = Rule-Based ∩ Embedding (agreement) 
           ∪ High-confidence from either method
           + Optional LLM verification for borderline cases
```

### Phase 4: Storage & Export (GSoC Weeks 8–9)
> **Goal**: Produce clean, reproducible outputs

- JSON export: Prettified, schema-validated
- CSV export: Flat format with tags as comma-separated values
- Incremental update workflow (detect new FOAs, skip already processed)
- FAISS vector index for similarity search (stretch goal)

### Phase 5: Evaluation (GSoC Weeks 9–10)
> **Goal**: Demonstrate tagging quality with metrics

- Hand-label **25–50 FOAs** as gold standard (you + a friend/mentor)
- Compute per-tag precision, recall, F1
- Inter-rater agreement (Cohen's kappa if 2+ annotators)
- Error analysis and improvement suggestions

### Phase 6: Documentation & Polish (GSoC Weeks 10–12)
> **Goal**: Make the project production-ready and well-documented

- Complete README with setup instructions
- API documentation
- Design decision document
- Reproducibility guide
- Final demo video/notebook

---

## 4. Screening Task Strategy 🎯

### Requirements Recap
Build `main.py` that:
```bash
python main.py --url "<FOA_URL>" --out_dir ./out
```

Outputs:
- `out/foa.json` — Structured FOA data
- `out/foa.csv` — Same data in CSV format

### Implementation Strategy

The screening task should demonstrate:
1. **Clean, modular code** — Show software engineering skills
2. **Smart data extraction** — Handle both API and webpage sources
3. **Rule-based tagging** — Even basic tagging shows NLP awareness
4. **Proper error handling** — Edge cases matter
5. **Documentation** — README + inline comments

### Screening Task Flow

```
URL Input → Detect Source (Grants.gov? NSF?) 
         → Fetch via API (preferred) or scrape HTML
         → Extract fields into schema
         → Apply rule-based semantic tags
         → Export JSON + CSV
```

### Key URLs to Support for Screening Task
- `https://www.grants.gov/search-results-detail/<OPPORTUNITY_ID>`
- `https://www.nsf.gov/awardsearch/showAward?AWD_ID=<AWARD_ID>`

### What Will Impress the Mentors
1. **Using the Grants.gov API** instead of raw scraping (shows research)
2. **Pydantic schema validation** (shows software engineering maturity)
3. **Even basic ontology tags** (shows you understand the NLP scope)
4. **Tests** (even 2-3 tests show professionalism)
5. **Clean git history** with meaningful commits

---

## 5. Technical Deep Dives

### 5.1 Grants.gov API Usage

```python
import requests

GRANTS_GOV_SEARCH_URL = "https://api.grants.gov/v1/api/search2"
GRANTS_GOV_FETCH_URL = "https://api.grants.gov/v1/api/fetchOpportunity"

def search_opportunities(keyword: str, page: int = 1):
    """Search Grants.gov for funding opportunities."""
    payload = {
        "keyword": keyword,
        "oppStatuses": "forecasted|posted",
        "sortBy": "openDate|desc",
        "rows": 25,
        "offset": (page - 1) * 25
    }
    response = requests.post(GRANTS_GOV_SEARCH_URL, json=payload)
    response.raise_for_status()
    return response.json()

def fetch_opportunity(opp_id: int):
    """Fetch detailed opportunity data by ID."""
    payload = {"oppId": opp_id}
    response = requests.post(GRANTS_GOV_FETCH_URL, json=payload)
    response.raise_for_status()
    return response.json()
```

### 5.2 NSF Awards API Usage

```python
NSF_API_URL = "https://api.nsf.gov/services/v1/awards.json"

def search_nsf_awards(keyword: str, start_date: str = None):
    """Search NSF awards API."""
    params = {
        "keyword": keyword,
        "printFields": "id,title,agency,startDate,expDate,abstractText,fundsObligatedAmt",
        "resultsPerPage": 25,
    }
    if start_date:
        params["dateStart"] = start_date  # Format: MM/DD/YYYY
    
    response = requests.get(NSF_API_URL, params=params)
    response.raise_for_status()
    return response.json()
```

### 5.3 Semantic Tagging with Embeddings

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class EmbeddingTagger:
    def __init__(self, ontology: dict, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.ontology = ontology
        self._build_reference_embeddings()
    
    def _build_reference_embeddings(self):
        """Pre-compute embeddings for ontology terms."""
        self.tag_names = []
        self.tag_texts = []
        
        for category, tags in self.ontology.items():
            for tag in tags:
                name = tag if isinstance(tag, str) else list(tag.keys())[0]
                synonyms = tag[name].get("synonyms", []) if isinstance(tag, dict) else []
                text = f"{name} {' '.join(synonyms)}"
                self.tag_names.append(f"{category}/{name}")
                self.tag_texts.append(text)
        
        self.reference_embeddings = self.model.encode(self.tag_texts)
    
    def tag(self, text: str, threshold: float = 0.35) -> list:
        """Tag text using embedding similarity."""
        query_embedding = self.model.encode([text])
        similarities = cosine_similarity(query_embedding, self.reference_embeddings)[0]
        
        tags = []
        for i, sim in enumerate(similarities):
            if sim >= threshold:
                tags.append({
                    "tag": self.tag_names[i],
                    "confidence": float(sim),
                    "method": "embedding"
                })
        
        return sorted(tags, key=lambda x: x["confidence"], reverse=True)
```

### 5.4 FOA Schema (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
import uuid

class SemanticTag(BaseModel):
    tag: str                         # e.g., "research_domains/artificial_intelligence"
    confidence: float = Field(ge=0, le=1)
    method: str                      # "rule_based" | "embedding" | "llm"

class FOARecord(BaseModel):
    foa_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    agency: str
    open_date: Optional[date] = None
    close_date: Optional[date] = None
    eligibility: Optional[str] = None
    program_description: Optional[str] = None
    award_range_min: Optional[float] = None
    award_range_max: Optional[float] = None
    source_url: str
    source: str                      # "grants_gov" | "nsf"
    semantic_tags: List[SemanticTag] = []
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 6. GSoC Proposal Tips 📝

### What Mentors Look For
1. **Understanding of the problem** — Show you know WHY this matters
2. **Technical depth** — Demonstrate you've researched the APIs, NLP techniques
3. **Realistic timeline** — Don't overcommit; include buffer weeks
4. **Previous work** — Link to your relevant projects (NLP, scraping, embeddings)
5. **Screening task quality** — This is your FIRST impression

### Proposal Structure (Recommended)
1. **Title & Synopsis** (1 paragraph)
2. **Problem Statement** (why this matters, who benefits)
3. **Proposed Solution** (architecture diagram, tech choices)
4. **Implementation Plan** (weekly breakdown with milestones)
5. **Technical Approach**
   - Data sources + API strategy
   - Schema design
   - Tagging methodology (rule-based vs embedding vs LLM)
   - Evaluation strategy
6. **Stretch Goals** (show ambition: FAISS, CLI search, additional sources)
7. **About Me** (relevant skills, projects, contributions)
8. **Timeline** (aligned with GSoC schedule)

### Common Mistakes to Avoid
- ❌ Copying the project description verbatim
- ❌ Not completing the screening task
- ❌ Proposing a timeline without implementation details
- ❌ Not showing understanding of the NLP/ML components
- ❌ Not linking relevant previous work

### How to Stand Out
- ✅ Show a working screening task with **clean code + tests**
- ✅ Propose a clear, well-defined ontology (not vague)
- ✅ Demonstrate embedding similarity with a small example
- ✅ Show awareness of edge cases (missing dates, multi-agency FOAs)
- ✅ Contribute to HumanAI Foundation's GitHub before proposing

---

## 7. Timeline & Milestones

### Pre-GSoC (NOW → March)
| Week | Task | Deliverable |
|------|------|------------|
| Week 1 | Set up project + understand APIs | Working API test scripts |
| Week 2 | Build screening task | `main.py` + `foa.json` + `foa.csv` |
| Week 3 | Polish + write README | Submit screening task + CV |
| Week 4 | Write GSoC proposal | Draft proposal |
| Week 5 | Review + iterate proposal | Final proposal submission |

### GSoC Period (June–August, ~12 weeks)
| Phase | Weeks | Focus | Deliverable |
|-------|-------|-------|-------------|
| 1 | 1–3 | Ingestion pipeline | 2 working source connectors |
| 2 | 3–5 | Extraction + normalization | Schema-validated FOA records |
| 3 | 5–8 | Semantic tagging | Rule-based + embedding taggers |
| 4 | 8–9 | Export + storage | JSON/CSV export + update workflow |
| 5 | 9–10 | Evaluation | Gold standard + metrics report |
| 6 | 10–12 | Docs + polish + stretch goals | Production-ready pipeline |

---

## 🎯 Immediate Next Steps

1. **Set up the project** — Create virtual env, install dependencies
2. **Test the APIs** — Make your first Grants.gov and NSF API calls
3. **Build the screening task** — This is your PRIORITY
4. **Write the proposal** — Use this plan as your blueprint
5. **Submit early** — Don't wait until the last day!

---

*Last updated: 2026-02-20*
*Project: AI-Powered Funding Intelligence (FOA Ingestion + Semantic Tagging)*
*Organization: Human AI Foundation / ISSR / University of Alabama*
