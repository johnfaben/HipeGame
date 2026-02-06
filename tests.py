import unittest

from sqlalchemy import create_engine
from app import app, db
from app.models import User, Hipe, Answer


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.ctx = app.app_context()
        self.ctx.push()
        # Swap in an in-memory SQLite engine so tests never touch app.db
        self._orig_engine = db._app_engines[app][None]
        db._app_engines[app][None] = create_engine('sqlite://')
        db.create_all()
        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        # Restore the real engine
        db._app_engines[app][None] = self._orig_engine
        self.ctx.pop()

    def test_solve_hipe(self):
        u = User(username='Alice', email='alice@alice.com')
        h = Hipe('hq')
        a = Answer('earthquake')
        a.hipe_id = 1
        db.session.add(u)
        db.session.add(h)
        db.session.add(a)
        db.session.commit()

        assert not u.has_solved(h)
        u.solve(h)
        db.session.commit()
        assert u.has_solved(h)

    def test_follow(self):
        u = User(username='Alice', email='alice@alice.com')
        v = User(username='Bob', email='bob@bob.com')
        db.session.add(u)
        db.session.add(v)
        db.session.commit()

        assert not u.is_following(v)
        u.follow(v)
        db.session.commit()
        assert u.is_following(v)

        u.unfollow(v)
        db.session.commit()
        assert not u.is_following(v)


if __name__ == '__main__':
    unittest.main()
