import requests  #requests lets Python act like a client

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

def fetch_books_by_genre(genre, max_results=10):
    params = {
        "q" : f"subject:{genre}",
        "maxResults": max_results,
        "printType": "books"
    }

    response = requests.get(GOOLE_BOOKS_API_URL, params=params)

    if response.status_code != 200:
        return []
    
    data = response.json()
    books = []

    for item in data.get("items", []):
        volume = item.get("volumeInfo", {})
#We DO NOT pass raw API responses to UI.
#Instead, we create:
        book = {
            "title": volume.get("title"),
            "authors": volume.get("authors", []),
            "description": volume.get("description"),
            "average_rating": volume.get("averageRating"),
            "ratings_count": volume.get("ratingsCount", 0),
            "thumbnail": volume.get("imageLinks", {}).get("thumbnail")
        }

        books.append(book)

    return books
