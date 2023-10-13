"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

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


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id

class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            Message.query.filter_by(text="Hello").one()

    def test_add_message__fail(self):
        """Test if adding a message fails and redirects to form
          if no text is supplied
        """

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", follow_redirects=True)
            html = resp.get_data(as_text=True)


            self.assertEqual(resp.status_code, 200)
            self.assertIn("On create message form", html)
            self.assertEqual(Message.query.count(), 1)

    def test_show_message(self):
        """Test for success in showing message"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get(f'/messages/{self.m1_id}')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("m1-text", html)

    def test_show_message_fail(self):
        """Test for 404 for showing a message that does not exist"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get('/messages/doesnotexist')

        self.assertEqual(resp.status_code, 404)

    def test_delete_message(self):
        """Test success delete message"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.post(f'/messages/{self.m1_id}/delete', follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Message.query.count(), 0)
        self.assertIn('On user detail page', html)

    def test_delete_message_fail(self):
        """Test if deleting a message that does not belong to you fails"""

        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.add(u2)
        db.session.commit()

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = u2.id

        resp = c.post(f'/messages/{self.m1_id}/delete', follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(Message.query.count(), 1)
        self.assertIn("Unauthorized", html)

    def test_like_success(self):
        """Test success of liking a message"""

        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.add(u2)
        db.session.commit()

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = u2.id

        resp = c.post(f'/messages/{self.m1_id}/like', data={"from-url":f"http://localhost:5000/"})

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Like.query.count(), 1)
        self.assertEqual(len(u2.liked_messages), 1)
        self.assertEqual(u2.liked_messages[0].user_id, self.u1_id)


    def test_unlike_success(self):
        """Test success of unliking a message"""

        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.add(u2)
        db.session.commit()

        m1 = Message.query.get(self.m1_id)
        u2.liked_messages.append(m1)

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = u2.id

        resp = c.post(f'/messages/{self.m1_id}/like', data={"from-url":f"http://localhost:5000/"})

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Like.query.count(), 0)
        self.assertEqual(len(u2.liked_messages), 0)

    def test_like_own_message(self):
        """Test if liking a message written by you fails"""
        
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        u1 = User.query.get(self.u1_id)
        resp = c.post(
            f'/messages/{self.m1_id}/like',
            data={"from-url":f"http://localhost:5000/"},
            follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Like.query.count(), 0)
        self.assertEqual(len(u1.liked_messages), 0)
        self.assertIn("Cannot like your own post", html)
















