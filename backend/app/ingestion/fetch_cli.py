import argparse
import json
import os
import sys
from .europe_pmc import EuropePMCClient
from .manifest import DocumentManifest


def main():
    parser = argparse.ArgumentParser(description="Fetch and ingest biomedical papers from Europe PMC")
    parser.add_argument("--query", type=str, required=True, help="Biomedical search query, e.g. 'BRAF melanoma resistance'")
    parser.add_argument("--limit", type=int, default=5, help="Number of articles to fetch (default: 5)")
    parser.add_argument("--output-dir", type=str, default="data/raw/papers", help="Directory to save parsed article JSONs")
    parser.add_argument("--db-path", type=str, default="data/metadata.db", help="SQLite database for document manifest")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    manifest = DocumentManifest(db_path=args.db_path)

    print(f"\n🔍 Querying Europe PMC for: '{args.query}' (Limit: {args.limit})")
    with EuropePMCClient() as client:
        articles = client.search_and_ingest(args.query, limit=args.limit)

    if not articles:
        print("❌ No articles fetched.")
        return

    saved_count = 0
    for art in articles:
        file_name = f"{art.id.replace('/', '_')}.json"
        file_path = os.path.join(args.output_dir, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(art.model_dump_json(indent=2))

        manifest.add_article(art, file_path=file_path)
        saved_count += 1
        print(f"  ✅ Ingested: {art.id} | Sections: {len(art.sections)} | {art.metadata.title[:70]}...")

    stats = manifest.get_stats()
    print(f"\n🎉 Successfully ingested {saved_count} articles.")
    print(f"📊 Corpus Summary: Total Articles: {stats['total_articles']} | Fulltext: {stats['fulltext_articles']} | Sections: {stats['total_sections']}")


if __name__ == "__main__":
    main()
