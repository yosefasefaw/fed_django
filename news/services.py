import os
import requests

url = "https://eventregistry.org/api/v1/article/"


def create_payload(
    page_number,
    articles_count,
    api_key=os.getenv("EVENTREGISTRY_API_KEY"),
    date_start=None,
    date_end=None,
):
    # Default to recent window if not provided, or handle None gracefully?
    # Existing code had hardcoded string. Let's default to a safe value or just use what's passed.

    date_filter = {}
    if date_start and date_end:
        # Convert datetime objects to string format 'YYYY-MM-DD' if they aren't already strings
        formatted_start = (
            date_start.strftime("%Y-%m-%d")
            if hasattr(date_start, "strftime")
            else date_start
        )
        formatted_end = (
            date_end.strftime("%Y-%m-%d") if hasattr(date_end, "strftime") else date_end
        )

        date_filter = {"dateStart": formatted_start, "dateEnd": formatted_end}
    else:
        # Fallback to hardcoded or leave empty?
        # User wants "possibility to retrieve".
        # Let's keep the hardcoded as default fallback if desired, or just default to today?
        # For safety, let's keep the user's manual edit as fallback if they run script directly without args.
        date_filter = {"dateStart": "2026-01-25", "dateEnd": "2026-01-26"}

    payload = {
        "action": "getArticles",
        "query": {
            "$query": {
                "$and": [
                    {
                        "$or": [
                            {
                                "conceptUri": "http://en.wikipedia.org/wiki/Federal_funds_rate"
                            },
                            {
                                "$and": [
                                    {
                                        "conceptUri": "http://en.wikipedia.org/wiki/Federal_Open_Market_Committee"
                                    },
                                    {
                                        "keyword": "US Federal Reserve",
                                        "keywordLoc": "body",
                                    },
                                ]
                            },
                        ]
                    },
                    date_filter,
                ]
            },
            "$filter": {"startSourceRankPercentile": 0, "endSourceRankPercentile": 30},
        },
        "articlesPage": page_number,
        "articlesCount": articles_count,
        "resultType": "articles",
        "articlesSortBy": "date",
        "includeArticleSocialScore": True,
        "includeArticleConcepts": True,
        "includeArticleCategories": True,
        "includeArticleLocation": True,
        "includeArticleImage": True,
        "includeArticleVideos": True,
        "includeArticleLinks": True,
        "includeArticleExtractedDates": True,
        "includeArticleDuplicateList": True,
        "includeArticleOriginalArticle": True,
        "includeConceptImage": True,
        "includeConceptDescription": True,
        "includeConceptSynonyms": True,
        "includeConceptTrendingScore": True,
        "includeSourceDescription": True,
        "includeSourceLocation": True,
        "includeSourceRanking": True,
        "apiKey": api_key,  # <- keep this secret
    }
    return payload


def retrieve_articles(
    date_start, date_end, page_numbers=1, articles_count=5, api_key=None
):
    url = "https://eventregistry.org/api/v1/article/"
    total_data = []
    for page_number in list(range(1, page_numbers + 1)):
        print(f"starting to create a payload for page_number {page_number}")
        payload_args = {
            "page_number": page_number,
            "articles_count": articles_count,
            "date_start": date_start,
            "date_end": date_end,
        }
        if api_key:
            payload_args["api_key"] = api_key

        payload = create_payload(**payload_args)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        number_of_articles = len(response.json().get("articles", {}).get("results", []))
        if number_of_articles == 0:
            print(f"No more data:{page_number} has {number_of_articles} articles")
            break
        if response.status_code == 200:
            total_data.extend(response.json().get("articles", {}).get("results", []))

    print(f"total data: {len(total_data)}")
    return total_data
