import requests
import json
import re

def scrape_justwatch(query):
    # Fake being a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # JustWatch GraphQL Endpoint (reverse engineered)
    url = "https://apis.justwatch.com/graphql"
    
    # GraphQL Query for searching
    payload = {
        "operationName": "GetSuggestedTitles",
        "variables": {
            "country": "IN",
            "language": "en",
            "first": 1,
            "filter": {"searchQuery": query}
        },
        "query": """
        query GetSuggestedTitles($country: Country!, $language: Language!, $first: Int!, $filter: TitleFilter) {
          popularTitles(country: $country, filter: $filter, first: $first) {
            edges {
              node {
                id
                objectId
                objectType
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
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        data = res.json()
        edges = data.get('data', {}).get('popularTitles', {}).get('edges', [])
        
        if edges:
            node = edges[0]['node']
            content = node['content']
            
            # Format poster URL
            poster_template = content.get('posterUrl')
            poster = f"https://images.justwatch.com{poster_template.replace('{profile}', 's592')}" if poster_template else None
            
            # Extract Platforms
            platforms = []
            seen = set()
            for offer in node.get('offers', []):
                m_type = offer.get('monetizationType')
                pkg = offer.get('package', {})
                name = pkg.get('clearName')
                if name and name not in seen:
                    platforms.append({
                        "name": name,
                        "type": m_type.capitalize() if m_type else "Stream",
                        "icon": f"https://images.justwatch.com{pkg.get('icon').replace('{profile}', 's100')}" if pkg.get('icon') else ""
                    })
                    seen.add(name)
            
            return {
                "title": content.get('title'),
                "overview": content.get('shortDescription'),
                "rating": content.get('scoring', {}).get('imdbScore') if content.get('scoring') else None,
                "poster": poster,
                "platforms": platforms
            }
        else:
            return None
    except Exception as e:
        print(f"Scrape error: {e}")
        return None

results = scrape_justwatch("Leo 2023")
print(json.dumps(results, indent=2))
