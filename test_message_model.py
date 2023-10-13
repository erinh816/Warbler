"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follow
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.commit()

        m1 = Message(text="This is m1", user_id=u1.id)

        db.session.add(m1)
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id


    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Test that m1 exists in Message and was written by u1"""

        u1 = User.query.get(self.u1_id)
        m1 = Message.query.get(self.m1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 1)
        self.assertEqual(m1.text, "This is m1")
        self.assertEqual(Message.query.count(), 1)
        self.assertEqual(u1.messages[0], m1)

    def test_create_message_fail(self):
        """Test if creating a message fails if text is not supplied"""

        new_message = Message(user_id= self.u1_id)

        with self.assertRaises(IntegrityError):
            db.session.add(new_message)
            db.session.commit()

        db.session.rollback()
        
        self.assertEqual(Message.query.count(), 1)

    def test_is_liked(self):
        """Test the is_liked method success"""

        u2 = User.query.get(self.u2_id)
        m1 = Message.query.get(self.m1_id)

        u2.liked_messages.append(m1)
        db.session.commit()

        is_liked = u2.is_liked(self.m1_id)

        self.assertTrue(is_liked)
        self.assertEqual(len(u2.liked_messages), 1)

    def test_is_liked_false(self):
        """Test for if a message has not been liked"""
        u2 = User.query.get(self.u2_id)

        is_liked = u2.is_liked(self.m1_id)

        self.assertFalse(is_liked)
        self.assertEqual(len(u2.liked_messages), 0)






