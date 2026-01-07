import wikipedia

def fetch_wiki_data(query, sentences=5):
    """
    Fetches a summary from Wikipedia for the given query.
    """
    try:
        # Search for the best match
        search_results = wikipedia.search(query)
        if not search_results:
            return None
        
        # Get the page of the first result
        page = wikipedia.page(search_results[0], auto_suggest=False)
        return {
            "title": page.title,
            "summary": page.summary[:1000], # Limit length
            "url": page.url,
            "images": page.images[:5] # Get some image URLs for reference
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Pick the first option if ambiguous
        try:
             page = wikipedia.page(e.options[0], auto_suggest=False)
             return {
                "title": page.title,
                "summary": page.summary[:1000],
                "url": page.url,
                 "images": page.images[:5]
            }
        except:
            return None
    except Exception as e:
        print(f"Wikipedia fetch error for {query}: {e}")
        return None

def get_research_context(bike_model):
    """
    Aggregates research data for a bike model.
    """
    print(f"Researching: {bike_model}...")
    wiki_data = fetch_wiki_data(bike_model)
    
    context = ""
    if wiki_data:
        context += f"**Wikipedia Summary for {wiki_data['title']}:**\n{wiki_data['summary']}\n\n"
        context += f"**Source:** {wiki_data['url']}\n"
    else:
        context += "No specific Wikipedia data found. Rely on general knowledge.\n"
        
    return context
