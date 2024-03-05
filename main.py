from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators
import requests

API = "e94ca8316f5f843329782d0959b58bee"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlOTRjYTgzMTZmNWY4NDMzMjk3ODJkMDk1OWI1OGJlZSIsInN1YiI6IjY1ZTZkYjVjMWRiNjVkMDE4NzkzYWM5YSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.ckrVajCWgPEgdsxoBAI4v6QRrbqf8t8XqYWyYmrWqSQ"
}
app = Flask(__name__)
app.config['SECRET_KEY'] = 'deepak'
Bootstrap5(app)


class UpdateForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 eg: 7.5 ", [validators.InputRequired()])
    review = StringField("You review ", [validators.InputRequired()])
    submit = SubmitField("Submit", [validators.InputRequired()])


class AddForm(FlaskForm):
    movie_title = StringField("Movie Title", [validators.InputRequired()])
    submit_button = SubmitField("Submit")


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top_10_movies_of_all.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


##CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    m_title = db.Column(db.String(250), unique=True, nullable=False, )
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/edit", methods=["POST", "GET"])
def update():
    form = UpdateForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie)


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddForm()
    if form.validate_on_submit():
        movie_title = form.movie_title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": API, "query": movie_title}, headers=headers)
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": API, "language": "hi-IN"}, headers=headers)
        data = response.json()
        print(type(data))
        print(data)
        new_movie = Movie(
            m_title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("home", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
