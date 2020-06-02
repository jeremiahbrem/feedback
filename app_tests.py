from unittest import TestCase
from flask import session

from app import app
from models import db, User, Feedback

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///flask_feedback_test'
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

db.drop_all()
db.create_all()

class UserViewsTestCase(TestCase):
    """Testing User view functions"""

    def setUp(self):
        """Add sample User data."""

        db.create_all()
        
        user = User.register(username="jlbrem", password="iloveastronomy", email="jeremiahbrem@gmail.com", 
                             first_name="Jeremiah", last_name="Brem")
        feedback = Feedback(title="Betelgeuse",content="It's big and red", username="jlbrem")
        db.session.add_all([user, feedback])
        db.session.commit()

        self.user = User.query.first()
        self.feedback = Feedback.query.first()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()
        db.drop_all()

    def test_register_redirect(self):
        """Testing redirection to register"""

        with app.test_client() as client:
            resp = client.get("/", follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Create Your Account", html)

    def test_get_register(self):
        """Testing if registration form page is displayed"""

        with app.test_client() as client:
            resp = client.get("/register")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Create Your Account", html)

    def test_get_register_logged_in(self):
        """Testing redirect to user profile is already logged in"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulate login
                change_session['username'] = "jlbrem"
            resp = client.get("/register", follow_redirects=True)
            html = resp.get_data(as_text=True)     
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("User Profile: jlbrem", html)
            change_session.pop("username")

    def test_get_register_post(self):
        """Testing if user profile page is displayed after new user registration"""

        with app.test_client() as client:
            data = {"username": "bremj", "password": "lookatstars", "email": "jlbrem@gmail.com", 
                    "first_name": "Jerry", "last_name": "Bremy"}
            resp = client.post("/register", data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("User Profile: bremj", html)

    def test_invalid_register(self):
        """Testing redirect to form page after invalid input"""

        with app.test_client() as client:
            data = {"username": "bremj", "password": "iloveastronomy2", "email": "ggfufgygftyf",
                "first_name": "Jeremiah2", "last_name": "Brem2"}
            resp = client.post("/register", data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Create Your Account", html)

    def test_show_user_no_login(self):
        """Testing redirect to form page if no logged in user"""

        # no user_id in session
        with app.test_client() as client:
            resp = client.get("/users/jlbrem", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Create Your Account", html)
            self.assertIn("You must be logged in to view!", html)

    def test_get_login(self):
        """Testing display of login form page"""

        with app.test_client() as client:
            resp = client.get("/login")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Login", html)

    def test_get_login_logged_in(self):
        """Testing redirect to user profile if already logged in"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulate login
                change_session['username'] = "jlbrem"
            resp = client.get("/login", follow_redirects=True)
            html = resp.get_data(as_text=True)     
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("User Profile: jlbrem", html) 
            change_session.pop("username")       

    def test_get_login_post(self):
        """Testing redirect to user profile page after user login"""

        with app.test_client() as client:

            resp = client.post("/login", data={
                                               "username": "jlbrem", 
                                               "password": "iloveastronomy"
                                              },
                                         follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("User Profile: jlbrem", html)            

    def test_logout(self):
        """Testing if user logs out and is redirected to create account page"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulating login
                change_session['username'] = "jlbrem"
            resp = client.get("/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Create Your Account", html)
            change_session.pop("username")

    def test_show_user(self):
        """Testing if user profile page displays"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulating user login
                change_session['username'] = "jlbrem"
            resp = client.get("/users/jlbrem", follow_redirects=True)
            html = resp.get_data(as_text=True)      

            self.assertEqual(resp.status_code, 200)
            self.assertIn("User Profile: jlbrem", html)
            change_session.pop("username")

    def test_delete_user(self):
        """Testing deletion of user and redirect to create account/login page"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulating user login
                change_session['username'] = "jlbrem"
            resp = client.post("/users/jlbrem/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)      

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Create Your Account", html)
            self.assertIn("User deleted!", html)
            self.assertIsNone(Feedback.query.get(self.feedback.id))
            change_session.pop("username")     

    def test_show_update_feedback(self):
        """Testing display of update feedback form"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulating user login
                change_session['username'] = "jlbrem"      
            resp = client.get(f"/feedback/{self.feedback.id}/update", follow_redirects=True)
            html = resp.get_data(as_text=True)  

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit Betelgeuse", html)
            self.assertIn("User: jlbrem", html)
            change_session.pop("username")

    def test_show_update_feedback_post(self)       :
        """Testing update of feedback and redirect to user page""" 

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulating user login
                change_session['username'] = "jlbrem"      
            data = {"title": "Betelgeuse", "content": "Will it go supernova??"}    
            resp = client.post(f"/feedback/{self.feedback.id}/update", data=data,follow_redirects=True)
            html = resp.get_data(as_text=True)  

            self.assertEqual(resp.status_code, 200)
            self.assertIn("User Profile: jlbrem", html)
            self.assertIn("Feedback updated!", html)
            change_session.pop("username")
    
    def test_show_add_feedback(self):
        """Testing display of add new feedback form"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulating user login
                change_session['username'] = "jlbrem"         
            resp = client.get(f"/users/{self.user.username}/feedback/add", follow_redirects=True)
            html = resp.get_data(as_text=True)  

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Add New Feedback", html)
            self.assertIn("User: jlbrem", html)
            change_session.pop("username")
    
    def test_delete_feedback(self):
        """Testing deletion of feedback and redirect to user page"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                # simulating user login
                change_session['username'] = "jlbrem"          
            resp = client.post(f"/feedback/{self.feedback.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)  

            self.assertEqual(resp.status_code, 200)
            self.assertIn("User Profile: jlbrem", html)
            self.assertIn("Feedback deleted!", html)
            self.assertIsNone(Feedback.query.get(self.feedback.id))
            change_session.pop("username")

    def test_enter_email(self):
        """Testing if enter email form is displayed to reset password"""

        with app.test_client() as client:
            resp = client.get("/password/email")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Enter Your Email to Reset Password", html)

    def test_enter_email_post(self):
        """Testing redirect to check email page after form submission"""

        with app.test_client() as client:
            resp = client.post("/password/email", data={"email": "jeremiahbrem@gmail.com"}, 
                                follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please check your email for a link to reset your password", html)     

    def test_show_reset(self):
        """Testing if reset password form is shown after user clicks link with token"""

        with app.test_client() as client:
            self.user.password_reset = "testtoken"

            resp = client.get("/password/reset?key=testtoken")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Reset Your Password", html)