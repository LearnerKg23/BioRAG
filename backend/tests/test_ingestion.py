import pytest
from backend.app.ingestion.xml_parser import JATSArticleParser, normalize_section_type
from backend.app.ingestion.manifest import DocumentManifest
from backend.app.models.article import Article, ArticleMetadata, ArticleSection


SAMPLE_JATS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Archiving and Interchange DTD v1.2 20190208//EN" "JATS-archivearticle1.dtd">
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front>
    <article-meta>
      <article-id pub-id-type="pmid">38123456</article-id>
      <article-id pub-id-type="pmc">PMC10800001</article-id>
      <article-id pub-id-type="doi">10.1038/s41586-024-00001-x</article-id>
      <title-group>
        <article-title>Mechanisms of BRAF V600E Resistance in Metastatic Melanoma</article-title>
      </title-group>
      <contrib-group>
        <contrib contrib-type="author">
          <name><surname>Curie</surname><given-names>Marie</given-names></name>
        </contrib>
        <contrib contrib-type="author">
          <name><surname>Fleming</surname><given-names>Alexander</given-names></name>
        </contrib>
      </contrib-group>
      <pub-date>
        <year>2024</year>
      </pub-date>
      <abstract>
        <p>Acquired resistance to BRAF inhibitors remains a major therapeutic barrier in melanoma patients harboring the V600E mutation.</p>
      </abstract>
      <kwd-group>
        <kwd>Melanoma</kwd>
        <kwd>BRAF</kwd>
        <kwd>Drug Resistance</kwd>
      </kwd-group>
    </article-meta>
  </front>
  <body>
    <sec sec-type="intro">
      <title>Introduction</title>
      <p>Targeted therapy with dabrafenib and trametinib initially produces high response rates in patients with BRAF V600-mutated melanoma.</p>
    </sec>
    <sec sec-type="methods">
      <title>Materials and Methods</title>
      <p>Patient-derived melanoma cell lines were treated with dabrafenib (100 nM) for 48 hours to assess downstream ERK phosphorylation.</p>
    </sec>
    <sec sec-type="results">
      <title>Results</title>
      <p>Reactivation of the MAPK pathway was observed in 78% of resistant clones through novel secondary mutations in NRAS or MEK1.</p>
      <p>Combination treatment with ERK inhibitors restored apoptosis in 85% of resistant lines.</p>
    </sec>
    <sec sec-type="discussion">
      <title>Discussion</title>
      <p>Our findings indicate that vertical pathway suppression can overcome single-agent resistance mechanisms in clinical settings.</p>
    </sec>
  </body>
</article>
"""


def test_section_normalization():
    assert normalize_section_type("Materials and Methods") == "methods"
    assert normalize_section_type("Results and Analysis") == "results"
    assert normalize_section_type("Discussion") == "discussion"
    assert normalize_section_type("Concluding Remarks") == "conclusion"
    assert normalize_section_type("Background") == "introduction"
    assert normalize_section_type("Statistical Analysis") == "other"


def test_jats_parser_metadata():
    article = JATSArticleParser.parse(SAMPLE_JATS_XML)

    assert article.id == "PMC10800001"
    assert article.metadata.pmid == "38123456"
    assert article.metadata.pmcid == "PMC10800001"
    assert article.metadata.doi == "10.1038/s41586-024-00001-x"
    assert article.metadata.title == "Mechanisms of BRAF V600E Resistance in Metastatic Melanoma"
    assert "Marie Curie" in article.metadata.authors
    assert "Alexander Fleming" in article.metadata.authors
    assert article.metadata.publication_year == 2024
    assert "Melanoma" in article.metadata.mesh_terms
    assert "Acquired resistance to BRAF inhibitors" in article.abstract


def test_jats_parser_sections():
    article = JATSArticleParser.parse(SAMPLE_JATS_XML)

    assert len(article.sections) == 4
    section_titles = [s.title for s in article.sections]
    assert "Introduction" in section_titles
    assert "Materials and Methods" in section_titles
    assert "Results" in section_titles
    assert "Discussion" in section_titles

    results_sec = next(s for s in article.sections if s.section_type == "results")
    assert "Reactivation of the MAPK pathway was observed" in results_sec.content
    assert "restored apoptosis in 85%" in results_sec.content


def test_document_manifest(tmp_path):
    db_file = tmp_path / "test_manifest.db"
    manifest = DocumentManifest(db_path=str(db_file))

    article = JATSArticleParser.parse(SAMPLE_JATS_XML)
    assert not manifest.is_ingested(article.id)

    success = manifest.add_article(article, file_path="/fake/path.json")
    assert success
    assert manifest.is_ingested(article.id)
    assert manifest.is_ingested("38123456")

    retrieved = manifest.get_article(article.id)
    assert retrieved is not None
    assert retrieved["title"] == article.metadata.title
    assert len(retrieved["authors"]) == 2

    stats = manifest.get_stats()
    assert stats["total_articles"] == 1
    assert stats["fulltext_articles"] == 1
    assert stats["total_sections"] == 4
