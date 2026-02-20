# FOA Intelligence 🧠🔬

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GSoC 2026](https://img.shields.io/badge/GSoC-2026-orange.svg)](https://humanai.foundation/gsoc/projects/2026/project_ISSR.html)
[![API Status](https://img.shields.io/website?up_message=online&url=https%3A%2F%2Ffoa-api.onrender.com%2Fdocs)](https://foa-api.onrender.com/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-Powered Funding Intelligence — FOA Ingestion + Semantic Tagging**

A production-grade pipeline that automatically ingests Funding Opportunity Announcements (FOAs) from public sources, extracts structured fields, and applies ontology-based semantic tags to support institutional research discovery and grant matching.

---

## ⚡ Live Production Endpoints

| Service | Environment | URL |
|---------|-------------|-----|
| **Web Dashboard** | Production | [https://foa-dashboard.onrender.com/](https://foa-dashboard.onrender.com/) |
| **API Documentation** | Swagger UI | [https://foa-api.onrender.com/docs](https://foa-api.onrender.com/docs) |

---

## 🌟 Visual Overview

![Project Dashboard](assets/images/image.png)
*Real-time Discovery and Tagging Interface*

### 🎬 System Demo
![FOA Intelligence Demo](assets/video/foa%20intelligence.gif)

---

## 📐 Architecture & Scale

The system is designed with a modular, source-agnostic architecture capable of processing thousands of FOAs with high precision.

```mermaid
graph TD
    A[Public URLs / Keywords] --> B{Source Detection}
    B -- "grants.gov" --> C[Grants.gov API]
    B -- "nsf.gov" --> D[NSF Awards API]
    C --> E[Raw Data]
    D --> E
    E --> F[Pydantic Schema Extraction]
    F --> G[Semantic Tagging Engine]
    subgraph Tagging Engine
        G1[Rule-Based Matcher]
        G2[Embedding Similarity]
        G3[Probabilistic Ensemble]
    end
    G --> G1 & G2 & G3
    G1 & G2 & G3 --> H[Tag Fusion & Validation]
    H --> I[JSON / CSV / Vector Export]
    I --> J[Streamlit Dashboard]
    I --> K[FastAPI Endpoints]
```

---

## 🚀 Key Features

- **Multi-Source Ingestion**: Native integration with Grants.gov and NSF REST APIs.
- **Microservice Architecture**: Decoupled FastAPI backend and Streamlit frontend.
- **Hierarchical Ontology**: 30+ semantic tags across 4 categories (Domains, Methods, Populations, Themes).
- **Hybrid Tagging**: Combines deterministic keyword matching with semantic embedding similarity (`all-MiniLM-L6-v2`).
- **Production Ready**: Full validation using Pydantic, comprehensive logging, and automated deployment via Render.

---

## 📁 Project Structure

```
FOA-Intelligence/
├── api.py                   # FastAPI Production Backend
├── app.py                   # Streamlit Interactive UI
├── main.py                  # Pipeline Orchestration Logic
├── render.yaml              # Infrastructure-as-Code (Render)
├── demo.ipynb               # Technical Deep-Dive Notebook
├── config/                  # Ontology & System Settings
├── src/                     # Core Engine Architecture
│   ├── ingestion/           # Source Adapters (API/Scrapers)
│   ├── extraction/          # Schema & Normalization
│   └── tagging/             # NLP & Semantic Engine
└── assets/                  # Media & Visual documentation
```

---

## 🛠️ Tech Stack & Reliability

- **Frameworks**: FastAPI, Streamlit, Pydantic
- **NLP/ML**: Sentence-Transformers, Scikit-Learn, PyYAML
- **Infrastructure**: Render Blueprint, GitHub Actions Ready
- **Data**: RESTful API Integration, JSON/CSV Serialization

---

## 🧪 Development & Evaluation

### Local Setup
```bash
pip install -r requirements.txt
python main.py --search "artificial intelligence" --max-results 5
```

### Run Tests
```bash
pytest tests/ -v
```

---

## 🙏 Acknowledgments

- **Human AI Foundation** — GSoC 2026 Mentoring Org
- **ISSR, University of Alabama** — Research & Mentorship
- **Grants.gov** & **NSF** — Data Providers