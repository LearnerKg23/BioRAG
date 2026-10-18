import re
import unicodedata


LIGATURES = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬅ": "ft",
    "ﬆ": "st",
}

# Regex to strip noisy reference tags like "[1]", "[1, 2]", "[12-15]", while preserving things like "p[53]" or "MAPK[1]"
CITATION_BRACKETS_REGEX = re.compile(r"\[(?:\d+(?:\s*[-–,]\s*\d+)*)\]")

# Author-year citations like "(Smith et al., 2021)" or "(Johnson and Lee, 2018)"
AUTHOR_YEAR_CITATION_REGEX = re.compile(
    r"\([A-Z][a-zA-Z\s]+(?:et al\.?|and [A-Z][a-zA-Z\s]+)?,\s*(?:19|20)\d{2}[a-z]?\)"
)


class BiomedicalTextCleaner:
    """Preprocesses and normalizes biomedical scientific texts while strictly protecting domain entities."""

    @classmethod
    def clean(cls, text: str, strip_citations: bool = True) -> str:
        if not text:
            return ""

        # 1. Normalize Unicode (preserve greek letters like α, β, γ)
        cleaned = unicodedata.normalize("NFKC", text)

        # 2. Replace ligatures
        for lig, repl in LIGATURES.items():
            cleaned = cleaned.replace(lig, repl)

        # 3. Normalize quotes and dashes
        cleaned = cleaned.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        cleaned = cleaned.replace("–", "-").replace("—", "-")

        # 4. Optional citation stripping
        if strip_citations:
            cleaned = CITATION_BRACKETS_REGEX.sub("", cleaned)
            cleaned = AUTHOR_YEAR_CITATION_REGEX.sub("", cleaned)

        # 5. Clean up duplicate spaces and whitespace artifacts
        cleaned = re.sub(r"\s+([,.;:\)])", r"\1", cleaned)
        cleaned = re.sub(r"\(\s+", "(", cleaned)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
        return cleaned.strip()
