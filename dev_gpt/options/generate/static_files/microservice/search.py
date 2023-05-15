import os
from typing import Any, List, Optional

from googleapiclient.discovery import build

google_api_key: Optional[str] = os.environ['GOOGLE_API_KEY']
google_cse_id: Optional[str] = os.environ['GOOGLE_CSE_ID']
search_engine = build("customsearch", "v1", developerKey=google_api_key)

k: int = 10
siterestrict: bool = False

def _google_search_results(search_term: str, **kwargs: Any) -> List[dict]:
    cse = search_engine.cse()
    if siterestrict:
        cse = cse.siterestrict()
    res = cse.list(q=search_term, cx=google_cse_id, **kwargs).execute()
    return res.get("items", [])

def run(query: str) -> str:
    """Run query through GoogleSearch and parse result."""
    snippets = []
    results = _google_search_results(query, num=k)
    if len(results) == 0:
        return "No good Google Search Result was found"
    for result in results:
        if "snippet" in result:
            snippets.append(result["snippet"])

    return " ".join(snippets)


if __name__ == "__main__":
    # google-api-python-client==2.86.0
    print(run("jina ai"))