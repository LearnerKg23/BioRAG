import logging
import time
from typing import List, Optional, Dict, Any
import httpx
from ..models.article import Article, ArticleMetadata, ArticleSection
from .xml_parser import JATSArticleParser

logger = logging.getLogger(__name__)


class EuropePMCClient:
    """Client for Europe PMC REST API to query and download biomedical research literature."""

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=self.timeout, follow_redirects=True)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def search_articles(
        self,
        query: str,
        limit: int = 10,
        open_access_only: bool = True,
        sort: str = "CITED desc",
    ) -> List[Dict[str, Any]]:
        """Search Europe PMC for scientific literature."""
        search_query = query.strip()
        if open_access_only and "OPEN_ACCESS:" not in search_query:
            search_query = f"({search_query}) AND (OPEN_ACCESS:y)"

        url = f"{self.BASE_URL}/search"
        params = {
            "query": search_query,
            "format": "json",
            "pageSize": min(limit, 100),
            "resultType": "core",
            "sort": sort,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                result_list = data.get("resultList", {}).get("result", [])
                logger.info(f"Europe PMC search returned {len(result_list)} articles for query: '{query}'")
                return result_list[:limit]
            except Exception as e:
                logger.warning(f"Europe PMC search attempt {attempt} failed: {e}")
                if attempt == self.max_retries:
                    logger.error(f"Failed to query Europe PMC after {self.max_retries} attempts.")
                    return []
                time.sleep(1.0 * attempt)
        return []

    def fetch_fulltext_xml(self, pmcid: str) -> Optional[str]:
        """Fetch the full-text JATS XML for an open access paper given its PMCID."""
        clean_pmcid = pmcid.strip().upper()
        if not clean_pmcid.startswith("PMC"):
            clean_pmcid = f"PMC{clean_pmcid}"

        url = f"{self.BASE_URL}/{clean_pmcid}/fullTextXML"

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(url)
                if response.status_code == 200 and response.text.strip():
                    return response.text
                elif response.status_code == 404:
                    logger.info(f"Full-text XML not available for {clean_pmcid} (404)")
                    return None
            except Exception as e:
                logger.warning(f"Failed to fetch XML for {clean_pmcid} on attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    return None
                time.sleep(1.0 * attempt)
        return None

    def ingest_article_by_pmcid(self, pmcid: str) -> Optional[Article]:
        """Fetch and parse an article into an Article domain model."""
        xml_text = self.fetch_fulltext_xml(pmcid)
        if not xml_text:
            return None
        return JATSArticleParser.parse(xml_text, fallback_id=pmcid)

    def search_and_ingest(self, query: str, limit: int = 10) -> List[Article]:
        """Search Europe PMC and ingest eligible open-access full-text articles."""
        search_results = self.search_articles(query, limit=limit, open_access_only=True)
        articles: List[Article] = []

        for item in search_results:
            pmcid = item.get("pmcid")
            pmid = item.get("pmid")
            title = item.get("title", "Untitled")
            abstract = item.get("abstractText", "")

            # If PMCID is present, attempt full-text JATS XML parsing
            if pmcid:
                try:
                    art = self.ingest_article_by_pmcid(pmcid)
                    if art:
                        # If parsed metadata missed journal or year, backfill from search item
                        if not art.metadata.journal:
                            art.metadata.journal = item.get("journalTitle")
                        if not art.metadata.publication_year and item.get("pubYear"):
                            try:
                                art.metadata.publication_year = int(item.get("pubYear"))
                            except ValueError:
                                pass
                        articles.append(art)
                        logger.info(f"Ingested full-text article: {pmcid} - '{title[:60]}...' ({len(art.sections)} sections)")
                        continue
                except Exception as e:
                    logger.warning(f"Error parsing full-text XML for {pmcid}: {e}. Falling back to abstract.")

            # Fallback to abstract-only Article if full-text is not available
            authors_str = item.get("authorString", "")
            authors = [a.strip() for a in authors_str.split(",") if a.strip()] if authors_str else []
            pub_year = None
            if item.get("pubYear"):
                try:
                    pub_year = int(item.get("pubYear"))
                except ValueError:
                    pass

            meta = ArticleMetadata(
                pmid=pmid,
                pmcid=pmcid,
                doi=item.get("doi"),
                title=title,
                authors=authors,
                journal=item.get("journalTitle"),
                publication_year=pub_year,
                is_open_access=bool(item.get("isOpenAccess") == "Y"),
                url=f"https://europepmc.org/article/MED/{pmid}" if pmid else None,
            )

            fallback_sections = []
            if abstract:
                fallback_sections.append(
                    ArticleSection(
                        title="Abstract",
                        section_type="abstract",
                        content=abstract,
                        order=0
                    )
                )

            art = Article(
                id=pmcid or pmid or item.get("id", "UNKNOWN"),
                metadata=meta,
                abstract=abstract or "",
                sections=fallback_sections,
            )
            articles.append(art)
            logger.info(f"Ingested abstract-only article: {pmid or pmcid} - '{title[:60]}...'")

        return articles
