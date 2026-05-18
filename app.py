from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from collections import Counter
import requests
from services.google_books import fetch_book_by_title, fetch_books_from_google

app = Flask(__name__)

app.secret_key = "saha-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///saha.db"
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    books = db.relationship("Book", backref="owner", lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))
    genre = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    thumbnail = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

@app.route("/")
def home():
    return render_template("welcome.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if len(username.strip()) < 3:
            flash("Username must contain at least 3 characters", "error")
            return redirect(url_for("signup"))
        
        if len(email) < 10 or not email.endswith("@gmail.com"):
            flash("Enter avalid email address", "error")
            return redirect(url_for("signup"))
        
        if len(password) < 3:
            flash("Password must contain at least 3 characters", "error")
            return redirect(url_for("signup"))

        #check if email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered. Please login.", "error")
            return redirect(url_for("signup"))
        
        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        ) 
        db.session.add(new_user)
        db.session.commit()

        #auto login after signup
        session["user_id"] = new_user.id

        flash("Signup successful! Welcome to Saha 💖", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
    
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for("login"))
        
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = db.session.get(User, session["user_id"])
    books = Book.query.filter_by(user_id=user.id).all()

    recommended_genre = None

    recommended_books = []
    
    if books:
        #smart genre weight system
        genre_score = {}

        for book in books:
            if not book.genre:
                continue

            genre = book.genre.split(",")[0].strip()

            #weight based on rating
            if book.rating == 5:
                score = 5
            elif book.rating == 4:
                score = 3
            elif book.rating == 3:
                score = 2
            else:
                score = 1

            genre_score[genre] = genre_score.get(genre, 0) + score

        #sort genres by score
        sorted_genres = sorted(genre_score.items(), key=lambda x: x[1], reverse=True)

        if sorted_genres:
            recommended_genre = sorted_genres[0][0]

        #FETCH BOOKS FROM GOOGLE
        fetched_titles = set()

        for g in sorted_genres[:3]:
            genre_name = g[0]
            books_from_api = fetch_books_from_google(genre_name)

            if books_from_api:
                for b in books_from_api:
                    if b["title"] not in fetched_titles:
                        recommended_books.append(b)
                        fetched_titles.add(b["title"])

    return render_template("dashboard.html", 
                           user=user, 
                           books=books, 
                           recommended_genre=recommended_genre,
                           recommended_books = recommended_books)

@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":

        title = request.form["title"]

        # CHECK IF THE BOOK ALREADY EXISTS FOR THIS USER
        existing_book = Book.query.filter_by(
            user_id=session["user_id"]
        ).filter(
            db.func.lower(Book.title) == title.lower()
        ).first()

        if existing_book:
            flash("This book already exists in your library 📚", "error")
            return redirect(url_for("dashboard"))
        
        # fetch from google using title only
        fetched_author, thumbnail, fetched_genre = fetch_book_by_title(title)

        # safe fallback
        if not fetched_author:
            fetched_author = "Unknown"

        if not fetched_genre:
            fetched_genre = "General"

        new_book = Book(
            title=title,
            author=fetched_author,
            genre=fetched_genre,
            rating=int(request.form.get("rating", 0)),
            thumbnail=thumbnail,
            user_id=session["user_id"]
        )

        db.session.add(new_book)
        db.session.commit()

        flash("Book added successfully ✨", "success")
        return redirect(url_for("dashboard"))
    
    return render_template("add_book.html")

@app.route("/delete-book/<int:book_id>")
def delete_book(book_id):

    if "user_id" not in session:
        return redirect(url_for("login"))
    
    book = Book.query.get_or_404(book_id)

    if book.user_id != session["user_id"]:
        flash("Unauthorized action", "error")
        return redirect(url_for("dashboard"))
    
    db.session.delete(book)
    db.session.commit()

    flash("Book removed successfully", "success")

    return redirect(url_for("dashboard"))

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return {"reply": "Please login first"}
    
    message = request.json.get("message")

    user = db.session.get(User, session["user_id"])
    books = Book.query.filter_by(user_id=user.id).all()

    if not books:
        return {"reply": "Add some books first so I can understand your taste 📚"}
    
    genres = [b.genre for b in books if b.genre]
    fav = Counter(genres).most_common(1)[0][0]

    reply = f"You seem to love {fav} books. Want some recommendations?"

    return {"reply": reply}

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
