"""User View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_user_views.py


import os
from unittest import TestCase
from unittest.mock import patch

from models import db, Message, User, Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id

class UserAddViewTestCase(UserBaseViewTestCase):

    def test_user_signup(self):
        with app.test_client() as c:
            data={"username": "testUser", "password":"password", "email":"test@test.com"}
            resp = c.post("/signup", data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            testUser = User.query.filter_by(username='testUser').one()

            print(testUser)
            self.assertEqual('testUser', testUser.username)
            self.assertNotEqual('password', testUser.password)
            self.assertIn("We're on the homepage(logged in)", html)
            self.assertEqual(User.query.count(), 3)

    def test_user_fail_signup(self):
        with app.test_client() as c:
            data={"password":"password", "email":"test@test.com"}
            resp = c.post("/signup", data=data)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn("We're on the signup page", html)
            self.assertEqual(User.query.count(), 2)

    def test_user_login(self):
        with app.test_client() as c:
            with patch("app.session", dict()) as session:
                data={"username":"u1", "password":'password'}
                resp = c.post("/login", data=data, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)

                user = User.query.filter_by(username='u1').one()

                self.assertIn("Hello, u1!", html)
                self.assertEqual(session[CURR_USER_KEY], user.id)

    def test_user_fail_login(self):
        with app.test_client() as c:
            data={"username":"u3", "password":'password'}
            resp = c.post("/login", data=data)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn("Invalid credentials.", html)
            self.assertIn("We are on login page", html)

    def search_users(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get('/users?q=u')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("@u1", html)
        self.assertIn("@u2", html)

    def search_users_no_result(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get('/users?q=DoesNotExist')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sorry, no users found", html)


    def test_show_logged_in_users_profile(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get(f'/users/{self.u1_id}')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("In Show user detail page", html)
        self.assertIn("Edit Profile", html)
        self.assertIn("Delete Profile", html)

    def test_show_any_user_profile(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get(f'/users/{self.u2_id}')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("In Show user detail page", html)
        self.assertIn("@u2", html)

    def test_show_following(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get(f'/users/{self.u1_id}/following')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("On following page", html)

    def test_show_followers(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get(f'/users/{self.u1_id}/followers')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("On followers page", html)

    def test_show_likes(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get(f'/users/{self.u1_id}/likes')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("On likes page", html)


