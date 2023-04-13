from flask__init__ import *
from sqlalchemy import Integer, Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import validators, StringField, PasswordField, IntegerField, TextAreaField

import requests


# ADD BOOKS TO LIST toread, wishlist, read

class FormAddBook(FlaskForm):
    ISBN = StringField('ISBN', [validators.DataRequired()])
    title = StringField('Book title', [validators.DataRequired()])
    author = StringField('Book author', [validators.DataRequired()])
    date = StringField('Year of publication')
    publisher = StringField('Publisher')
    Image_URL = StringField('Image_URL')

class ReadForm(FlaskForm):
    ISBN = StringField('ISBN')
    title = StringField('title')

class ReviewsForm(FlaskForm):
    rating = IntegerField('rating')
    review = TextAreaField('review')
    update_image = StringField('Update book display')


class ToReadBooks(db.Model):
    __tablename__ = 'to_read'
    id = Column('id', Integer, primary_key=True)
    ISBN = Column('ISBN', String, nullable=False)

    # linked account
    account_id = Column('account_id', Integer, ForeignKey('accounts.id'), nullable=False)  # creates many
    account = relationship('Accounts', back_populates='to_read_books')

class ReadBooks(db.Model):
    __tablename__ = 'read_books'
    id = Column('id', Integer, primary_key=True)
    ISBN = Column('ISBN', String, ForeignKey('books.ISBN'), nullable=False)
    book_parent = relationship('TableBooks')
    # create new columns for ratings and review
    rating = Column('rating', Integer, nullable=True)
    review = Column('review', Text, nullable=True)

    # linked account
    account_id = Column('account_id', Integer, ForeignKey('accounts.id'), nullable=False)  # creates many
    account = relationship('Accounts', back_populates='read_books')

class WishlistBooks(db.Model):
    __tablename__ = 'wishlist_books'
    id = Column('id', Integer, primary_key=True)
    ISBN = Column('ISBN', String, nullable=False)

    # linked account
    account_id = Column('account_id', Integer, ForeignKey('accounts.id'), nullable=False)  # creates many
    account = relationship('Accounts', back_populates='wishlist_books')


class BaseManager:
    """
    Manages the 'to-read' SQL table and Flask-form for entering new books.

    This function provides functionality for managing the 'to-read', 'read_books', or 'wishlist_books' tables in a SQL
    database and the corresponding Flask forms for users to enter new books. The function allows users
    to add new entries to the table, view the contents of the table, and delete entries
    from the table.

    Parameters:
        None

    Returns:
        None
    """
    def __init__(self, table_cls, form_cls):
        self.table = table_cls()
        self.form = form_cls()

    def self_populate(self, isbn=None):
        """
        Add a new book entry to the 'to-read' SQL table.

        This method adds a new book entry to the 'to-read' SQL table, using the ISBN
        provided by the user via the Flask form or the `isbn` parameter. If the ISBN is
        provided as a parameter, it takes precedence over the Flask form input. The new
        book entry is associated with the current user's account ID.

        Parameters:
            isbn (str): The ISBN of the book to be added to the table. If not provided,
            the method retrieves the ISBN from the Flask form.

        Returns:
            None
        """
        with app.app_context():
            self.table.account_id = current_user.id
            if isbn:
                self.table.ISBN = isbn
            else:
                self.table.ISBN = self.form['ISBN'].data
            db.session.add(self.table)
            db.session.commit()

class ToReadManager(BaseManager):
    def __init__(self):
        super().__init__(ToReadBooks, ReadForm)

class WishlistManager(BaseManager):
    def __init__(self):
        super().__init__(WishlistBooks, ReadForm)

class ReadBooksManager(BaseManager):
    def __init__(self):
        super().__init__(ReadBooks, ReadForm)

class ReviewManager:
    def __init__(self):
        self.table = ReadBooks()
        self.form = ReviewsForm()

    def self_populate(self, id):
        """
          Update a book review entry in the 'read' SQL table.

          This method updates an existing book review entry in the 'read' SQL table, using the
          ID of the review provided by the user via the Flask form. The method updates the
          rating and/or review text associated with the book review, as specified by the user
          input in the form. The method also updates the display image associated with the
          book, if specified by the user.

          Parameters:
              id (int): The ID of the book review to be updated.

          Returns:
              None
          """
        book_review = db.session.query(ReadBooks).filter_by(id=id).first()
        if self.form.rating.data:
            book_review.rating = self.form.rating.data
        if self.form.review.data:
            book_review.review = self.form.review.data
        # update display image
        if self.form.update_image.data:
            book = db.session.query(TableBooks).filter_by(ISBN=book_review.ISBN).first()
            book.Image_URL = self.form.update_image.data
        db.session.commit()


# AMAZON RELATED DATA

class Amazon_Users(db.Model):
    """User information no relationship to other database tables"""
    __tablename__ = 'users'
    user_id = Column('User_ID', Integer, primary_key=True)
    location = Column('Location', String, nullable=False)
    age = Column('Age', Integer, nullable=True)

    ratings = relationship('Amazon_Ratings', back_populates='user')

class Amazon_Ratings(db.Model):
    """Stored Amazon ISBN score values 0-10. Not linked to Accounts"""
    __tablename__ = 'ratings'
    id = Column('id', Integer, primary_key=True)
    rating = Column('Book_Rating', String, nullable=False)

    book_isbn = Column('ISBN', String, ForeignKey('books.ISBN'), nullable=False)  # creates many
    ISBN = relationship('TableBooks', back_populates='rating')  # one

    user_id = Column('user_id', Integer, ForeignKey('users.User_ID'), nullable=False)  # creates many
    user = relationship('Amazon_Users', back_populates='ratings')  # one


# ACCOUNTS

class Accounts(db.Model, UserMixin):
    """Website accounts with login extension"""
    __tablename__ = 'accounts'
    id = Column('id', Integer, primary_key=True)
    username = Column('username', String, nullable=False)
    password = Column('password', String, nullable=False)
    email = Column('email', String, nullable=True)

    hobbies = Column('hobbies', String, nullable=True)
    country = Column('country', String, nullable=True)
    about = Column('about', Text, nullable=True)

    to_read_books = relationship('ToReadBooks', back_populates='account')
    read_books = relationship('ReadBooks', back_populates='account')
    wishlist_books = relationship('WishlistBooks', back_populates='account')

class TableBooks(db.Model):
    __tablename__ = 'books'
    id = db.Column('id', db.Integer, primary_key=True)
    ISBN = db.Column('ISBN', db.String, nullable=False, unique=True)
    title = db.Column('Book_Title', db.String, nullable=False)
    author = db.Column('Book_Author', db.String, nullable=False)
    date = db.Column('Year_Of_Publication', db.String)
    publisher = db.Column('Publisher', db.String)
    Image_URL = db.Column('Image_URL', db.String)

    book_child = relationship('ReadBooks', back_populates='book_parent')
    rating = relationship('Amazon_Ratings', back_populates='ISBN')


class LoginForm(FlaskForm):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    # email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [validators.DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password',
                             [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')

class ProfileUpdate(FlaskForm):
    email = StringField('email')
    hobbies = StringField('hobbies')
    country = StringField('country')
    about = StringField('about')


class UserBase:
    """
    A base class for creating user objects in the application.

    Args:
        table_cls: The SQLAlchemy model class for the user table.
        form_cls: The Flask-WTF form class for creating user forms.

    Attributes:
        table: An instance of `table_cls` for the user.
        form: An instance of `form_cls` for creating user forms.

    Methods:
        self_populate(salted_pass: str): Populates the user's table with form data and a hashed password WHEN SPECIFIED*.

    """
    def __init__(self, table_cls, form_cls):
        self.table = table_cls()
        self.form = form_cls()

    def self_populate(self, salted_pass: str=None):
        """
         Populates the user's table with data from the Flask-WTF form and a hashed password.

         Args:
             salted_pass (str, optional): A hashed password for the user. Defaults to None.
         """
        with app.app_context():
            self.form.populate_obj(self.table)
            if salted_pass:
                self.table.password = salted_pass
            db.session.add(self.table)
            db.session.commit()

class LoginManager2(UserBase):
    def __init__(self):
        super().__init__(Accounts, LoginForm)

class RegisterManager(UserBase):
    def __init__(self):
        super().__init__(Accounts, RegisterForm)

class ProfileManager(UserBase):
    def __init__(self):
        super().__init__(Accounts, ProfileUpdate)

class AddBooksManager(UserBase):
    def __init__(self):
        super().__init__(TableBooks, FormAddBook)

    def open_library(self, isbn: str):
        """Searches the Open Library API for book resources that match the given ISBN
           and fills a new table entry with the book's information if found.

           Args:
               isbn (str): The ISBN of the book to search for.

           Returns:
               bool: True if book resources were found and added to the table, False otherwise.

           Raises:
               N/A

           Example:
               To search for book resources with ISBN '9780140449266':
               >> open_library('9780140449266')
           """
        url = 'https://openlibrary.org/api/books'
        params = {
            'bibkeys': isbn,
            'format': 'json',
            'jscmd': 'data'
        }
        book_info = requests.get(url, params=params).json()
        if not book_info:
            return False
        else:
            # handle unique constraints
            self.form.ISBN.data = isbn
            self.form.title.data = book_info[isbn]['title']
            self.form.author.data = book_info[isbn]['authors'][0]['name']
            self.form.date.data = book_info[isbn]['publish_date']
            if book_info[isbn].get('publisher'):
                self.form.Image_URL.data = book_info[isbn]['publishers'][0]['name']
            if book_info[isbn].get('cover'):
                self.form.Image_URL.data = book_info[isbn]['cover']['large']
            super.self_populate()
            return True


with app.app_context():
    db.create_all()