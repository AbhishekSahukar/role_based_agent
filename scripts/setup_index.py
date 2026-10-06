"""Create (or update) the policies index and upload data/policies.json.

Runs as whoever is signed in to the Azure CLI (no search keys).
Needs: Search Service Contributor + Search Index Data Contributor on the service.
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

ENDPOINT = os.environ["SEARCH_ENDPOINT"]
INDEX_NAME = os.getenv("SEARCH_INDEX", "policies")
DATA_FILE = ROOT / "data" / "policies.json"
KNOWN_ROLES = {"HR", "Employee", "IT"}  # must match the app role Values in Entra


def build_index() -> SearchIndex:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        # The security field: filterable, so queries can be trimmed by role.
        SimpleField(
            name="allowed_roles",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
        ),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
    ]
    return SearchIndex(name=INDEX_NAME, fields=fields)


def load_documents() -> list[dict]:
    docs = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for doc in docs:
        roles = doc.get("allowed_roles")
        # Fail closed: a typo like "hr" or an empty list would silently hide
        # or expose a document, so refuse to upload instead.
        if not roles or not set(roles) <= KNOWN_ROLES:
            sys.exit(f"Invalid allowed_roles {roles!r} in document {doc.get('id')!r}")
    return docs


def main():
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)

    SearchIndexClient(ENDPOINT, credential).create_or_update_index(build_index())
    print(f"index '{INDEX_NAME}' ready")

    docs = load_documents()
    results = SearchClient(ENDPOINT, INDEX_NAME, credential).merge_or_upload_documents(docs)
    failed = [r.key for r in results if not r.succeeded]
    print(f"uploaded {len(docs) - len(failed)} of {len(docs)} documents")
    if failed:
        sys.exit(f"failed: {failed}")


if __name__ == "__main__":
    main()