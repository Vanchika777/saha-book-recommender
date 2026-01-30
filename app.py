from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, redirect, url_for
from collections import Counter

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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))



@app.route("/")
def home():
    return "welcome"

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        ) 
        db.session.add(new_user)
        db.session.commit()

        print(User.query.all())

        return "Signup successful ❤️"

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
        else :
            return"Invalid email or password"
        
    return render_template("login.html")



@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    books = Book.query.filter_by(user_id=user.id).all()

    recommended_genre = None
    if books:
        genres = [book.genre for book in books if book.genre]

        if genres:
            recommended_genre = Counter(genres).most_common(1)[0][0]

    return render_template("dashboard.html", user=user, books=books, recommended_genre=recommended_genre)




@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        genre = request.form["genre"]
        rating = request.form["rating"]

        new_book = Book(
            title=title,
            author=author,
            genre=genre,
            rating=rating,
            user_id=session["user_id"]
        )

        db.session.add(new_book)
        db.session.commit()

        return redirect(url_for("dashboard"))
    
    return render_template("add_book.html")





@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
