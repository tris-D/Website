from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,EmailField,PasswordField
from wtforms.validators import DataRequired, URL, Email,Length
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class CreateUser(FlaskForm):
    email = EmailField("Enter your email...", validators=[DataRequired(),Email(message="Submit a valid email.")])
    password = PasswordField("Enter your password...",validators=[DataRequired(),Length(min=8,message="Must be at least 8 characters.")])
    name = StringField("Enter your name...",validators=[DataRequired()])
    submit = SubmitField("Register New User")


# TODO: Create a LoginForm to login existing users 
class LoginUser(FlaskForm):
    name = StringField("Username/Email",validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")

# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    body = CKEditorField("Write Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
