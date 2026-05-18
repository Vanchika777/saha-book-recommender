import requests

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

# -------- FETCH BY TITLE (when user adds book) ----------
def fetch_book_by_title(title):
    params = {
        "q": f"intitle:{title}",
        "maxResults": 1,
        "printType": "books",
        "key": "AIzaSyAlUZEDJEQzPExYBIcrwd5bLcJGdRF6PoU"
    }

    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=8)

        if response.status_code != 200:
            return "Unknown", "", "General"

        data = response.json()

        if "items" not in data:
            return "Unknown", "", "General"

        volume = data["items"][0]["volumeInfo"]

        author = volume.get("authors", ["Unknown"])[0]

        thumbnail = volume.get("imageLinks", {}).get("thumbnail", "")
        if thumbnail:
            thumbnail = thumbnail.replace("http://", "https://")

        genre = volume.get("categories", ["General"])[0]

        return author, thumbnail, genre

    except Exception as e:
        print("Google API error:", e)
        return "Unknown", "", "General"

# -------- FETCH BY GENRE (recommendation) ----------
def fetch_books_from_google(genre):
    params = {
        "q": f"subject:{genre}",
        "maxResults": 3,
        "printType": "books",
        "key": "AIzaSyAlUZEDJEQzPExYBIcrwd5bLcJGdRF6PoU"
    }

    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=8)

        if response.status_code != 200:
            return []

        data = response.json()
        books = []

        for item in data.get("items", []):
            volume = item.get("volumeInfo", {})

            title = volume.get("title", "No title")
            author = volume.get("authors", ["Unknown"])[0]

            image_links = volume.get("imageLinks", {})

            thumbnail = (
                image_links.get("thumbnail")
                or image_links.get("smallThumbnail")
                or "https://via.placeholder.com/120x180?text=No+Cover"
            )
            
            if thumbnail:
                thumbnail = thumbnail.replace("http://", "https://")

            books.append({
                "title": title,
                "author": author,
                "thumbnail": thumbnail
            })

        return books

    except Exception as e:
        print("Recommendation API error:", e)
        return []