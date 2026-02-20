"""
FOA Intelligence — AI-Powered Funding Intelligence Pipeline

CLI entry point for ingesting, extracting, tagging, and exporting
Funding Opportunity Announcements (FOAs).

Usage:
    python main.py --url "<FOA_URL>" --out_dir ./out
    python main.py --search "artificial intelligence" --source grants_gov --out_dir ./out
    python main.py --url "<FOA_URL>" --out_dir ./out --use-embeddings

Examples:
    # Ingest a single Grants.gov opportunity
    python main.py --url "https://www.grants.gov/search-results-detail/123456" --out_dir ./out

    # Ingest a single NSF award
    python main.py --url "https://www.nsf.gov/awardsearch/showAward?AWD_ID=2345678" --out_dir ./out

    # Search and ingest multiple FOAs
    python main.py --search "climate change" --source grants_gov --max-results 10 --out_dir ./out
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import date

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.grants_gov import GrantsGovIngestor
from src.ingestion.nsf import NSFIngestor
from src.extraction.schema import FOARecord
from src.tagging.rule_based import RuleBasedTagger
from src.tagging.ontology import Ontology
from src.export.exporters import export_json, export_csv
from config.settings import DEFAULT_OUTPUT_DIR, MAX_TAGS_PER_FOA


# ──────────────────────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("foa-intelligence")


# ──────────────────────────────────────────────────────────────
# Source Detection
# ──────────────────────────────────────────────────────────────
def detect_source(url: str) -> str:
    """Detect the FOA source from a URL."""
    url_lower = url.lower()
    if "grants.gov" in url_lower:
        return "grants_gov"
    elif "nsf.gov" in url_lower:
        return "nsf"
    else:
        logger.warning(f"Unknown source for URL: {url}. Defaulting to grants_gov.")
        return "grants_gov"


def get_ingestor(source: str):
    """Get the appropriate ingestor for the source."""
    ingestors = {
        "grants_gov": GrantsGovIngestor,
        "nsf": NSFIngestor,
    }
    ingestor_class = ingestors.get(source)
    if not ingestor_class:
        raise ValueError(f"Unknown source: {source}. Valid: {list(ingestors.keys())}")
    return ingestor_class()


# ──────────────────────────────────────────────────────────────
# Pipeline Orchestration
# ──────────────────────────────────────────────────────────────
def process_single_url(url: str, use_embeddings: bool = False) -> FOARecord:
    """
    Full pipeline for a single FOA URL:
    Ingest → Extract → Tag → Return FOARecord
    """
    # 1. Detect source and get ingestor
    source = detect_source(url)
    ingestor = get_ingestor(source)
    logger.info(f"Processing URL: {url} (source: {source})")

    # 2. Fetch raw data
    raw_data = ingestor.fetch_by_url(url)
    if not raw_data or raw_data.get("error"):
        error_msg = raw_data.get("error", "Unknown error") if raw_data else "No data returned"
        logger.error(f"Failed to fetch data: {error_msg}")
        raise RuntimeError(f"Ingestion failed: {error_msg}")

    # 3. Extract structured fields
    fields = ingestor.extract_fields(raw_data)
    logger.info(f"Extracted fields for: {fields.get('title', 'Unknown')[:80]}")

    # 4. Apply semantic tags
    tags = apply_tags(
        title=fields.get("title", ""),
        description=fields.get("program_description", ""),
        use_embeddings=use_embeddings,
    )
    fields["semantic_tags"] = tags[:MAX_TAGS_PER_FOA]

    # 5. Parse dates properly
    for date_field in ["open_date", "close_date"]:
        val = fields.get(date_field)
        if isinstance(val, str):
            try:
                fields[date_field] = date.fromisoformat(val)
            except (ValueError, TypeError):
                fields[date_field] = None

    # 6. Create FOARecord
    record = FOARecord(**fields)
    logger.info(
        f"✅ Processed: {record.title[:60]} | "
        f"{len(record.semantic_tags)} tags applied"
    )
    return record


def process_search(
    keyword: str,
    source: str,
    max_results: int = 10,
    use_embeddings: bool = False,
) -> list:
    """
    Search and process multiple FOAs.
    """
    ingestor = get_ingestor(source)
    logger.info(f"Searching {source} for: '{keyword}' (max: {max_results})")

    # Search
    raw_results = ingestor.search(keyword, max_results=max_results)
    logger.info(f"Found {len(raw_results)} results")

    records = []
    for i, raw_data in enumerate(raw_results):
        try:
            fields = ingestor.extract_fields(raw_data)

            # Apply tags
            tags = apply_tags(
                title=fields.get("title", ""),
                description=fields.get("program_description", ""),
                use_embeddings=use_embeddings,
            )
            fields["semantic_tags"] = tags[:MAX_TAGS_PER_FOA]

            # Parse dates
            for date_field in ["open_date", "close_date"]:
                val = fields.get(date_field)
                if isinstance(val, str):
                    try:
                        fields[date_field] = date.fromisoformat(val)
                    except (ValueError, TypeError):
                        fields[date_field] = None

            record = FOARecord(**fields)
            records.append(record)
            logger.info(f"  [{i+1}/{len(raw_results)}] {record.title[:60]}")

        except Exception as e:
            logger.warning(f"  [{i+1}/{len(raw_results)}] Failed: {e}")
            continue

    return records


def apply_tags(
    title: str,
    description: str,
    use_embeddings: bool = False,
) -> list:
    """
    Apply semantic tags using rule-based and optionally embedding-based methods.
    """
    ontology = Ontology()
    all_tags = []

    # Rule-based tagging (always run)
    rule_tagger = RuleBasedTagger(ontology=ontology)
    rule_tags = rule_tagger.tag(title, description)
    all_tags.extend(rule_tags)

    # Embedding-based tagging (optional, requires sentence-transformers)
    if use_embeddings:
        try:
            from src.tagging.embedding_tagger import EmbeddingTagger

            embed_tagger = EmbeddingTagger(ontology=ontology)
            embed_tags = embed_tagger.tag(title, description)
            all_tags.extend(embed_tags)
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Skipping embedding-based tagging."
            )

    # Deduplicate: keep highest confidence per tag
    seen = {}
    for tag in all_tags:
        key = tag.tag
        if key not in seen or tag.confidence > seen[key].confidence:
            seen[key] = tag

    return sorted(seen.values(), key=lambda t: t.confidence, reverse=True)


# ──────────────────────────────────────────────────────────────
# CLI Argument Parsing
# ──────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="FOA Intelligence — AI-Powered Funding Opportunity Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --url "https://www.grants.gov/search-results-detail/123456" --out_dir ./out
  python main.py --search "climate" --source grants_gov --out_dir ./out
  python main.py --url "https://www.nsf.gov/awardsearch/showAward?AWD_ID=2345678" --out_dir ./out
        """,
    )

    # Input mode (URL or search)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--url",
        type=str,
        help="URL of a single FOA to ingest (Grants.gov or NSF).",
    )
    input_group.add_argument(
        "--search",
        type=str,
        help="Keyword to search for FOAs.",
    )

    # Search options
    parser.add_argument(
        "--source",
        type=str,
        choices=["grants_gov", "nsf"],
        default="grants_gov",
        help="Source to search (default: grants_gov). Only used with --search.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of search results (default: 10).",
    )

    # Output
    parser.add_argument(
        "--out_dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory for JSON/CSV files (default: ./out).",
    )

    # Tagging options
    parser.add_argument(
        "--use-embeddings",
        action="store_true",
        help="Enable embedding-based semantic tagging (requires sentence-transformers).",
    )

    # Verbosity
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging.",
    )

    return parser.parse_args()


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Determine processing mode
        if args.url:
            # Single URL mode
            record = process_single_url(args.url, use_embeddings=args.use_embeddings)
            records = [record]
        else:
            # Search mode
            records = process_search(
                keyword=args.search,
                source=args.source,
                max_results=args.max_results,
                use_embeddings=args.use_embeddings,
            )

        if not records:
            logger.error("No FOA records were processed. Exiting.")
            sys.exit(1)

        # Export results
        json_path = export_json(records, out_dir / "foa.json")
        csv_path = export_csv(records, out_dir / "foa.csv")

        # Summary
        print("\n" + "=" * 60)
        print("  FOA Intelligence — Processing Complete")
        print("=" * 60)
        print(f"  Records processed : {len(records)}")
        print(f"  JSON output       : {json_path}")
        print(f"  CSV output        : {csv_path}")

        total_tags = sum(len(r.semantic_tags) for r in records)
        print(f"  Total tags applied : {total_tags}")

        if records:
            print(f"\n  Sample record:")
            r = records[0]
            print(f"    Title  : {r.title[:70]}")
            print(f"    Agency : {r.agency}")
            print(f"    Source : {r.source}")
            print(f"    Tags   : {len(r.semantic_tags)}")
            if r.semantic_tags:
                top = r.semantic_tags[0]
                print(f"    Top tag: {top.tag} (conf={top.confidence:.2f})")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
