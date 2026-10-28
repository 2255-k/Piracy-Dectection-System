import requests
import json

class MetadataService:
    def __init__(self):
        # We use JustWatch's open GraphQL endpoint. No API keys required.
        self.graphql_url = "https://apis.justwatch.com/graphql"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def scrape_justwatch(self, movie_name):
        """
        Reverse-engineered GraphQL call to JustWatch.
        Provides movie Title, Description, IMDb Rating, Poster, and Indian Streaming Platforms.
        """
        payload = {
            "operationName": "GetSuggestedTitles",
            "variables": {
                "country": "IN", # Hardcoded to India for your regional requirement
                "language": "en",
                "first": 1,
                "filter": {"searchQuery": movie_name}
            },
            "query": """
            query GetSuggestedTitles($country: Country!, $language: Language!, $first: Int!, $filter: TitleFilter) {
              popularTitles(country: $country, filter: $filter, first: $first) {
                edges {
                  node {
                    content(country: $country, language: $language) {
                      title
                      shortDescription
                      scoring {
                        imdbScore
                      }
                      posterUrl
                    }
                    offers(country: $country, platform: WEB) {
                      monetizationType
                      package {
                        clearName
                        icon
                      }
                    }
                  }
                }
              }
            }
            """
        }

        try:
            res = requests.post(self.graphql_url, json=payload, headers=self.headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                edges = data.get('data', {}).get('popularTitles', {}).get('edges', [])
                
                if edges:
                    node = edges[0]['node']
                    content = node.get('content', {})
                    
                    # Format poster URL (JustWatch returns a template with {profile})
                    poster_template = content.get('posterUrl')
                    poster = f"https://images.justwatch.com{poster_template.replace('{profile}', 's592')}" if poster_template else None
                    
                    # Extract Unique Platforms
                    platforms = []
                    seen = set()
                    for offer in node.get('offers', []):
                        m_type = offer.get('monetizationType')
                        pkg = offer.get('package', {})
                        name = pkg.get('clearName')
                        
                        if name and name not in seen:
                            # Format icon URL
                            icon_path = pkg.get('icon')
                            icon = f"https://images.justwatch.com{icon_path.replace('{profile}', 's100')}" if icon_path else ""
                            
                            platforms.append({
                                "name": name,
                                "type": m_type.capitalize() if m_type else "Stream",
                                "icon": icon
                            })
                            seen.add(name)
                    
                    return {
                        "id": "jw_result",
                        "title": content.get('title', movie_name.title()),
                        "overview": content.get('shortDescription', "No description available."),
                        "rating": content.get('scoring', {}).get('imdbScore') if content.get('scoring') else None,
                        "poster": poster,
                        "release_date": "N/A", # JustWatch payload didn't include release year, but that's fine
                        "platforms": platforms
                    }
            return self._get_simulated_details(movie_name)
        except Exception as e:
            print(f"JustWatch GraphQL error: {e}")
            return self._get_simulated_details(movie_name)

    def get_movie_details(self, movie_name):
        return self.scrape_justwatch(movie_name)

    def get_legal_platforms(self, movie_id, fallback_movie_name=""):
        # The scraping method returns platforms bundled together, 
        # but to keep app.py compatible without structural changes:
        res = self.scrape_justwatch(fallback_movie_name)
        return res.get("platforms", [])

    def _get_simulated_details(self, movie_name):
        # Fallback just in case they lose internet
        return {
            "id": None,
            "title": movie_name.title(),
            "overview": f"This is a fallback placeholder. We could not find live streaming info for {movie_name}.",
            "poster": "https://via.placeholder.com/500x750?text=No+Poster+Found",
            "rating": 0,
            "release_date": "N/A",
            "platforms": []
        }

metadata_service = MetadataService()
