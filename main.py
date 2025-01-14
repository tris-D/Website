from datetime import date,datetime
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm,CreateUser,LoginUser,CommentForm
from typing import List
hello
from dotenv import load_dotenv
import os

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id) # Function to find the user in user database?

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI','sqlite:///posts.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# TODO: Add Gravatar profile images # see Gravatar documentation for simple implementation into Python Flask app.
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) #First, this accepts the foreign key as the LINK, users table takes the id and will be linked to that User defined by the id
    author: Mapped["User"] = relationship("User", back_populates="blog_posts") # then the user object is linked to the author here

    blog_comments: Mapped[List["Comments"]] = relationship("Comments", back_populates="blog")

# TODO: Create a User table for all your registered users. 
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000), unique=True)

    blog_posts: Mapped[List['BlogPost']] = relationship('BlogPost', back_populates="author") # and the blog_posts that are linked to the author appears here as a list of all blogposts that have been created with that initial link by id
    blog_comments: Mapped[List['Comments']] = relationship('Comments',back_populates="commenter")
# TODO: Create a Comments table for all comments.
class Comments(db.Model):
    __tablename__ = "blog_comments"
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    date: Mapped[str] = mapped_column(String(250),nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    commenter: Mapped["User"] = relationship("User", back_populates="blog_comments")

    blog_id: Mapped[int] = mapped_column(ForeignKey("blog_posts.id"))
    blog:  Mapped["BlogPost"] = relationship("BlogPost", back_populates="blog_comments")

with app.app_context():
    db.create_all()

def admin_only(function):
    @wraps(function)  # this preserves the original function's properties
    def wrapper_function(*args,**kwargs):
        if current_user.is_authenticated:
            if current_user.id == 1:
                return function(*args,**kwargs)
            else:
                return 'Only admin account can edit blogs'
        else:
            flash('Log in as admin to access.')
            return redirect(url_for('login'))
    return wrapper_function

# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register',methods=['GET','POST'])
def register():
    form=CreateUser()
    if form.validate_on_submit():
        # check if the email is and name is unique
        existing_email = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        existing_name = db.session.execute(db.select(User).where(User.name == form.name.data)).scalar()
        if existing_email:
            flash('This email is already registered, please log in.')
            return redirect(url_for('login'))
        elif existing_name:
            flash('This name is already taken. Please alter or choose another one to register.')
            return redirect(url_for('register'))
        elif not existing_email and not existing_name:
            new_user = User(
                name = form.name.data,
                email = form.email.data,
                password = generate_password_hash(form.password.data,method='pbkdf2:sha256:600000',salt_length=16)
            )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html",form=form, logged_in = current_user.is_authenticated)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginUser()
    if form.validate_on_submit():
        email = form.name.data
        password = form.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user and check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        elif not user:
            flash('Email has not been registered. Try again?')
            return redirect(url_for('login'))  # this refreshes the page and displays the flash
        elif user and not check_password_hash(user.password,password):
            flash('Password is incorrect. Try again.') # this displays the flash without refreshing the page
    return render_template("login.html",form=form,logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('get_all_posts',logged_in=current_user.is_authenticated))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts,logged_in=current_user.is_authenticated,user=current_user)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>",methods=['GET','POST'])
def show_post(post_id):
    comment_form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)
    if comment_form.validate_on_submit():
        comment_to_add = Comments(
            body=comment_form.body.data,
            date= datetime.now().strftime("%d/%m/%Y"),
            user_id=current_user.id,
            blog_id=post_id,
        )
        db.session.add(comment_to_add)   # a query is an object or method used to interact with the database 
        db.session.commit() # like db.session.query(User).filter_by(name="Alex").first()/scalar(), notice how we also can use filter_by() and order_by(), creating a query() replaces .execute(db.select(User))
        return redirect(url_for('show_post',post_id=post_id))
    return render_template("post.html", post=requested_post,logged_in=current_user.is_authenticated,user=current_user,comment=comment_form)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only  # the order of this matters, because the decorator closest to the function, so bottom-up applies first
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            date=date.today().strftime("%B %d, %Y"),
            user_id = current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,logged_in=current_user.is_authenticated)


# TODO: Use a decorator so only an admin user can edit a post

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(  # see this over, this is how you put in the text without hardcoding it into the form data so that it is not changed even on submit
        title=post.title, 
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html",logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html",logged_in=current_user.is_authenticated)


if __name__ == "__main__":
    app.run(debug=False)
