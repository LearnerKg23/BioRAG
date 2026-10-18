import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from ..models.article import Article


class DocumentManifest:
    """Tracks ingested scientific publications, preventing duplicate downloads and indexing."""

    def __init__(self, db_path: str = "data/metadata.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    pmid TEXT,
                    pmcid TEXT,
                    doi TEXT,
                    title TEXT NOT NULL,
                    journal TEXT,
                    publication_year INTEGER,
                    is_open_access INTEGER DEFAULT 1,
                    has_fulltext INTEGER DEFAULT 0,
                    section_count INTEGER DEFAULT 0,
                    authors_json TEXT,
                    file_path TEXT,
                    ingested_at TEXT
                )
            """)
            conn.commit()

    def is_ingested(self, article_id: str) -> bool:
        """Check whether an article ID (PMCID or PMID) already exists in the manifest."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM articles WHERE id = ? OR pmid = ? OR pmcid = ?", (article_id, article_id, article_id))
            return cur.fetchone() is not None

    def add_article(self, article: Article, file_path: Optional[str] = None) -> bool:
        """Insert or update an ingested article in the manifest database."""
        now_str = datetime.now(timezone.utc).isoformat()
        has_fulltext = int(len(article.sections) > 1 or (len(article.sections) == 1 and article.sections[0].section_type != "abstract"))
        authors_json = json.dumps(article.metadata.authors)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO articles (
                    id, pmid, pmcid, doi, title, journal, publication_year,
                    is_open_access, has_fulltext, section_count, authors_json, file_path, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.id,
                article.metadata.pmid,
                article.metadata.pmcid,
                article.metadata.doi,
                article.metadata.title,
                article.metadata.journal,
                article.metadata.publication_year,
                int(article.metadata.is_open_access),
                has_fulltext,
                len(article.sections),
                authors_json,
                file_path or "",
                now_str
            ))
            conn.commit()
            return True

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM articles WHERE id = ? OR pmid = ? OR pmcid = ?", (article_id, article_id, article_id))
            row = cur.fetchone()
            if row:
                d = dict(row)
                d["authors"] = json.loads(d["authors_json"]) if d.get("authors_json") else []
                return d
            return None

    def list_articles(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM articles ORDER BY ingested_at DESC LIMIT ? OFFSET ?", (limit, offset))
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["authors"] = json.loads(d["authors_json"]) if d.get("authors_json") else []
                results.append(d)
            return results

    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), SUM(has_fulltext), SUM(section_count) FROM articles")
            total, fulltext, total_sections = cur.fetchone()
            return {
                "total_articles": total or 0,
                "fulltext_articles": fulltext or 0,
                "abstract_only_articles": (total or 0) - (fulltext or 0),
                "total_sections": total_sections or 0,
            }
