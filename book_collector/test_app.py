from __future__ import annotations

from collections.abc import Generator

import pytest
from flask.testing import FlaskClient

from app import Book, app, db


@pytest.fixture
def client() -> Generator[FlaskClient]:
    """Створює тестовий клієнт з in-memory базою даних."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()

        with app.test_client() as test_client:
            yield test_client

        db.session.remove()
        db.drop_all()


def test_home(client: FlaskClient) -> None:
    """Перевіряє доступність головної сторінки."""
    response = client.get('/')
    assert response.status_code == 200
    assert (
        b'Book Collector' in response.data
        or 'Привіт'.encode() in response.data
    )


def test_add_book_with_genre(client: FlaskClient) -> None:
    """Перевіряє додавання книги разом із жанром."""
    response = client.post(
        '/add',
        data={
            'title': 'Test Book',
            'author': 'Test Author',
            'year': 2023,
            'genre': 'Fantasy',
            'submit': True,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        book = Book.query.filter_by(title='Test Book').first()
        assert book is not None
        assert book.author == 'Test Author'
        assert book.genre == 'Fantasy'


def test_edit_book(client: FlaskClient) -> None:
    """Перевіряє редагування книги, включно зі зміною жанру."""
    with app.app_context():
        book = Book(
            title='Old Title',
            author='Old Author',
            genre='Drama',
            year=2020,
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = client.post(
        f'/edit/{book_id}',
        data={
            'title': 'New Title',
            'author': 'New Author',
            'year': 2021,
            'genre': 'Sci-Fi',
            'submit': True,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        updated_book = db.session.get(Book, book_id)
        assert updated_book is not None
        assert updated_book.title == 'New Title'
        assert updated_book.genre == 'Sci-Fi'


def test_list_books_with_genre(client: FlaskClient) -> None:
    """Перевіряє відображення жанру у списку книг."""
    with app.app_context():
        book = Book(title='List Test', author='Author', genre='Horror')
        db.session.add(book)
        db.session.commit()

    response = client.get('/books')
    assert response.status_code == 200
    assert b'List Test' in response.data
    assert b'Horror' in response.data


def test_search_books(client: FlaskClient) -> None:
    """Перевіряє пошук книг за назвою або автором."""
    with app.app_context():
        db.session.add_all([
            Book(title='Python Guide', author='John Doe', genre='Tech'),
            Book(title='Flask Basics', author='Jane Smith', genre='Tech'),
        ])
        db.session.commit()

    response = client.get('/books?q=Python')
    assert response.status_code == 200
    assert b'Python Guide' in response.data
    assert b'Flask Basics' not in response.data
