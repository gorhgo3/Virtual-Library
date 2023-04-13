from form_tables import *
from flask__init__ import db, app
from flask import redirect, url_for, flash, request, render_template
from flask_login import login_required, logout_user, current_user, LoginManager, login_user
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash

import random


@app.route('/')
def home():
    # TODO change homepage for logged in users to show recommended books based on their country
    # TODO show an overview of their library when logged in at homepage
    return render_template('homepage.html')

@app.route("/<user>-profile")
@login_required
def account_homepage(user):
    # review
    reviews = db.session.query(ReadBooks).filter(
        and_(ReadBooks.account_id == current_user.id, ReadBooks.rating >= 7)).all()
    if reviews:
        reviews = random.choice(seq=reviews)

    # wishlist
    wbook = db.session.query(WishlistBooks).filter_by(account_id=current_user.id).all()
    if wbook:
        wbook = random.choice(seq=wbook)
        wbook = db.session.query(TableBooks).filter_by(ISBN=wbook.ISBN).first()

    return render_template('userprofile.html', review=reviews, wishbook=wbook)


##############  ACCOUNT HANDLING ##############

@login_manager.user_loader
def load_user(user_id):
    user = db.session.query(Accounts).filter_by(id=user_id).first()
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Account login"""
    loginprocess = LoginManager2()
    if loginprocess.form.validate_on_submit():
        account = db.session.query(Accounts).filter_by(username=loginprocess.form['username'].data).first()
        if check_password_hash(account.password, password=loginprocess.form['password'].data):
            login_user(user=account)
            return redirect(url_for('account_homepage', user=current_user.username))
    return render_template('login.html', form=loginprocess.form)

@app.route('/logout')
@login_required
def logout():
    """Account logout"""
    logout_user()
    return redirect(url_for('home'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    """Register new Account"""
    registerprocess = RegisterManager()
    if registerprocess.form.validate_on_submit():
        secure = generate_password_hash(password=registerprocess.form['password'].data, method='pbkdf2:sha256',
                                        salt_length=16)
        registerprocess.self_populate(salted_pass=secure)
        return redirect(url_for('home'))
    return render_template('register.html', form=registerprocess.form)


##############  ACCOUNT BOOKS ##############

@app.route("/wishlist", methods=['GET', 'POST'])
@login_required
def wishlist():
    wishprocess = WishlistManager()
    if request.method == 'POST':
        ISBN = wishprocess.form['ISBN'].data
        title = wishprocess.form['title'].data
        # SEARCH EXISTING BOOKS
        if db.session.query(TableBooks).filter_by(ISBN=ISBN).first():
            wishprocess.self_populate()
            return redirect(url_for('account_homepage', user=current_user.username))
        elif db.session.query(TableBooks).filter_by(title=title).first():
            found_book = db.session.query(TableBooks).filter_by(title=title).first().ISBN
            wishprocess.self_populate(isbn=found_book)
            return redirect(url_for('account_homepage', user=current_user.username))
        else:
            # send this as post and assign ISBN to run the function of generating and backfilling the form sheet?
            # if ISBN:
            # else:
            return redirect(url_for('new_book', isbn=ISBN))
    return render_template('add.html', form=wishprocess.form, tag='wishlist')

@app.route("/to_read", methods=['GET', 'POST'])
@login_required
def to_read():
    toreadprocess = ToReadManager()
    if request.method == 'POST':
        ISBN = toreadprocess.form['ISBN'].data
        title = toreadprocess.form['title'].data
        # SEARCH EXISTING BOOKS
        if db.session.query(TableBooks).filter_by(ISBN=ISBN).first():
            toreadprocess.self_populate()
            return redirect(url_for('account_homepage', user=current_user.username))

        elif db.session.query(TableBooks).filter_by(title=title).first():
            found_book = db.session.query(TableBooks).filter_by(title=title).first().ISBN
            toreadprocess.self_populate(isbn=found_book)
            return redirect(url_for('account_homepage', user=current_user.username))
        # ADD NEW BOOK
        else:
            return redirect(url_for('new_book', isbn=ISBN))
    return render_template('add.html', form=toreadprocess.form, tag='to_read')

@app.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    """Add books the user has read"""
    readprocess = ReadBooksManager()
    if request.method == 'POST':
        title = readprocess.form['title'].data
        ISBN = readprocess.form['ISBN'].data

        if db.session.query(TableBooks).filter_by(ISBN=ISBN).first():
            readprocess.self_populate()
            return redirect(url_for('account_homepage', user=current_user.username))

        elif db.session.query(TableBooks).filter_by(title=title).first():
            found_book = db.session.query(TableBooks).filter_by(title=title).first().ISBN
            readprocess.self_populate(isbn=found_book)
            return redirect(url_for('account_homepage', user=current_user.username))
        else:
            # send to addbook route
            # flash('please help us find this book')
            return redirect(url_for('new_book', isbn=ISBN))
    return render_template('add.html', form=readprocess.form, tag='read')

    # return render_template('newbook.html', form=addprocess.form)

@app.route("/book_entry", methods=['GET', 'POST'])
@login_required
def new_book():
    temp = AddBooksManager()
    if request.args.get('isbn'):
        isbn = request.args.get('isbn')
        if temp.open_library(isbn):
            return redirect(url_for('account_homepage', user=current_user.username))
        # if temp.if book_information(isbn) (return True if successful)
        # fill the form out locally from temp.AddBooksManager instance
    if temp.form.validate_on_submit():
        temp.self_populate()
        return redirect(url_for('account_homepage', user=current_user.username))
    return render_template('newbook.html', form=temp.form)


##############  ACCOUNT REVIEWS ##############

@app.route("/bookreview/<bookid>", methods=['GET', 'POST'])
def review(bookid):
    reviewprocess = ReviewManager()
    if request.method == 'POST':
        reviewprocess.self_populate(bookid)
        return redirect(url_for('account_homepage', user=current_user.username))
    return render_template('review.html', form=reviewprocess.form)

@app.route("/delete/<obj>")
def delete(obj):
    book = db.session.query(ReadBooks).get(obj)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('account_homepage', user=current_user.username))


    # LOGIN REQUIRED ROUTES

@app.route("/edit/<id>", methods=["GET", "POST"])
@login_required
def account_profile_update(id):
    account_profile = ProfileUpdate()
    if request.method == 'POST':
        with app.app_context():
            user = db.session.query(Accounts).get(id)
            if bool(request.form['email']):
                user.email = request.form['email']
            if bool(request.form['hobbies']):
                user.hobbies = request.form['hobbies']
            if bool(request.form['country']):
                user.country = request.form['country']
            if bool(request.form['about']):
                user.about = request.form['about']
            db.session.commit()
        return redirect(url_for('account_homepage', user=current_user.username))
    elif request.method == 'GET':
        return render_template('profileupdate.html', form=account_profile)