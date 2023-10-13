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


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)
        self.assertEqual(len(u1.liked_messages),0)

    def test_is_following(self):
        '''test u1 is  following u2'''

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        db.session.commit()

        self.assertFalse(u1.is_following(u2))

        u1.following.append(u2)

        self.assertTrue(u1.is_following(u2))

        self.assertEqual(len(u1.following),1)
        self.assertEqual(len(u2.followers),1)

    def test_is_followed_by(self):
        '''test u1 is followed by u2'''
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        db.session.commit()

        self.assertFalse(u1.is_followed_by(u2))

        u2.following.append(u1)

        self.assertTrue(u1.is_followed_by(u2))

        self.assertEqual(len(u1.followers),1)
        self.assertEqual(len(u2.following),1)


    def test_user_signup(self):
        '''test signup class method success'''

        test_user = User.signup('testname', 'test@test.com', 'password', None)

        db.session.add(test_user)
        db.session.commit()

        self.assertEqual(test_user.username, 'testname')
        self.assertEqual(test_user.email, 'test@test.com')
        self.assertEqual(User.query.count(), 3)


    def test_user_signup(self):
        '''test signup class method fail'''

        test_user = User.signup('u1', 'test@test.com', 'password', None)

        with self.assertRaises(IntegrityError):
            db.session.commit()

        db.session.rollback()
        self.assertEqual(User.query.count(), 2)

    def test_user_authenticate(self):
        """Test successfull return when given valid username and password"""

        user = User.authenticate("u1", "password")

        self.assertIsInstance(user, User)
        self.assertNotEqual("password", user.password)
        self.assertEqual("u1", user.username)

    def test_user_authenticate_bad_username(self):

        user = User.authenticate("wrongusername", "password")

        self.assertFalse(user)

    def test_user_authenticate_bad_password(self):

        user = User.authenticate("u1", "wrongpassword")

        self.assertFalse(user)

    