from __future__ import annotations

from flask import Flask, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask.typing import ResponseReturnValue
from sqlalchemy import or_
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer)

    def __repr__(self) -> str:
        return f'<Book {self.title}>'


class BookForm(FlaskForm):
    title = StringField('Назва', validators=[DataRequired(), Length(max=150)])
    author = StringField('Автор', validators=[DataRequired(), Length(max=100)])
    year = IntegerField('Рік', validators=[NumberRange(min=0, max=2100)])
    genre = StringField('Жанр', validators=[Length(max=50)])
    submit = SubmitField('Додати книгу')


@app.route('/')
def home() -> str:
    """Повертає привітальне повідомлення на головній сторінці."""
    return 'Привіт, Book Collector!'


@app.route('/add', methods=['GET', 'POST'])
def add_book() -> ResponseReturnValue:
    """Додає нову книгу до колекції."""
    form = BookForm()
    if form.validate_on_submit():
        new_book = Book(
            title=form.title.data,
            author=form.author.data,
            year=form.year.data,
            genre=form.genre.data,
        )
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('list_books'))
    return render_template('add_book.html', form=form)


@app.route('/books')
def list_books() -> ResponseReturnValue:
    """Відображає список книг з опційним пошуком за назвою або автором."""
    query = request.args.get('q', '').strip()
    if query:
        books = Book.query.filter(
            or_(
                Book.title.ilike(f'%{query}%'),
                Book.author.ilike(f'%{query}%'),
            )
        ).all()
    else:
        books = Book.query.all()
    return render_template('list_books.html', books=books, query=query)


@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id: int) -> ResponseReturnValue:
    """Видаляє книгу за її ідентифікатором."""
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('list_books'))


@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id: int) -> ResponseReturnValue:
    """Редагує існуючу книгу, включно з полем жанру."""
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.year = form.year.data
        book.genre = form.genre.data
        db.session.commit()
        return redirect(url_for('list_books'))
    return render_template('add_book.html', form=form, edit=True)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
