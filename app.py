import os, secrets
from os import getenv
from flask_mail import Mail, Message
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, EnterEmailForm, ResetPasswordForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///flask_feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "s8t64h5gs3h1sdf35h4s"

load_dotenv()

# used .env file in project folder to store username and password for sending emails
# email server
# NOTE: Had to enable less secure apps in gmail security to work
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.environ.get('MAIL_USERNAME', None)
app.config["MAIL_PASSWORD"] = os.environ.get('MAIL_PASSWORD', None)

# administrator list
app.config["ADMINS"] = [app.config["MAIL_USERNAME"]]

mail = Mail(app)

connect_db(app)

db.create_all()

debug = DebugToolbarExtension(app)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

@app.route("/")
def register_redirect():
    """Redirects to register page route"""

    return redirect("/register")

@app.route("/register", methods=["GET", "POST"])
def get_register():
    """returns register form page"""

    # if logged in user, redirect to user profile page
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        return redirect(f"users/{user.username}")
    
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        user = User.register(username, password, email, first_name, last_name)
            
        db.session.add(user)
        db.session.commit()
        session["username"] = user.username

        return redirect(f"/users/{user.username}")

    return render_template("register.html", form=form)

@app.route("/users/<username>")
def show_user(username):
    """Returns user profile page"""

    if "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/")

    elif session["username"] == username:
        user = User.query.filter_by(username=username).first()
        if not user:
            return render_template("404.html")
        return render_template("user.html", user=user)

    else:
        return render_template("401.html")  

@app.route("/login", methods=["GET", "POST"])
def get_login():
    """Displays login form page"""

    # if logged in user, redirect to user profile page
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        if not user:
            return render_template("404.html")
        return redirect(f"users/{user.username}")

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        
        if user:
            session["username"] = user.username
            return redirect(f"/users/{user.username}")

        else:
            form.username.errors = ["Incorrect username or password"]

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    """Clears user from session and redirects to create account/login page"""

    session.pop("username")

    return redirect("/")  

@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    """Deletes user and redirects to create account/login page"""

    if "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/")

    elif session["username"] == username:
        user = User.query.filter_by(username=username).first()
        if not user:
            return render_template("404.html")
        db.session.delete(user)
        db.session.commit()
        session.pop("username")
        flash("User deleted!")
        return redirect("/")

    else:
        return render_template("401.html")

@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])    
def show_update_feedback(feedback_id):
    """Display user update feedback form"""

    feedback = Feedback.query.get(feedback_id)

    if not feedback:
        return render_template("404.html")
    
    elif "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/")

    user = feedback.user    
    
    if session.get("username", None) != user.username:
        return render_template("401.html")    

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
            
        db.session.commit()
        flash("Feedback updated!")

        return redirect(f"/users/{user.username}")

    return render_template("update_feedback.html", form=form, feedback=feedback)    

@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])    
def show_add_feedback(username):
    """Display user add feedback form"""

    form = FeedbackForm()

    user = User.query.filter_by(username=username).first()
    if not user:
            return render_template("404.html")

    elif "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/")
    
    elif session.get("username", None) != user.username: 
        return render_template("401.html")   

    elif form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title=title, content=content, username=user.username)
            
        db.session.add(feedback)
        db.session.commit()
        flash("Feedback added!")

        return redirect(f"/users/{user.username}")

    return render_template("add_feedback.html", form=form, user=user) 

@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Deletes feedback and redirects to user page"""

    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return render_template("404.html")
    user = feedback.user

    if "username" not in session:
        flash("You must be logged in!")
        return redirect("/")

    elif session.get("username", None) != user.username:
        return render_template("401.html")    

    else:
        db.session.delete(feedback)
        db.session.commit()
        flash("Feedback deleted!")
        return redirect(f"/users/{user.username}")

@app.route("/password/email", methods=["GET", "POST"])
def show_enter_email():
    """Shows enter email form to reset password"""

    form = EnterEmailForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email address doesn't exist")
            return redirect("/password/email")
        token = secrets.token_urlsafe(16)
        user.password_reset = token
        db.session.commit()

        msg = Message('Reset Password', sender = 'jeremiahbrem@gmail.com', recipients = [user.email])
        msg.body = """Cick on the link to reset your password:
                http://localhost:5000/password/reset?key=""" + token                  
        mail.send(msg)    

        return redirect(f"/password/check_email")

    return render_template("enter_email.html", form=form)

@app.route("/password/check_email")    
def show_check_email():
    """Sends email and displays check email page"""

    return render_template("check_email.html")

@app.route("/password/reset", methods=["GET", "POST"])
def show_reset():
    """Displays reset password form after user clicks reset link in email"""

    form = ResetPasswordForm()
    token = request.args.get("key")
    user = User.query.filter_by(password_reset=token).first()
    if not user or not token:
        return render_template("404.html")

    if form.validate_on_submit():
        password = form.password.data
        user.password = User.hashed_new_password(password)
        user.password_reset = None
        db.session.commit()
        flash("Password reset. Please login.")
        return redirect("/login")

    else:
        return render_template("reset_password.html", form=form)    
