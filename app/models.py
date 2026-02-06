from app import db
from sqlalchemy.sql import func
from flask_login import UserMixin


followers = db.Table('followers',
        db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
        )

solvers = db.Table('solvers',
        db.Column('solver_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('hipe_id', db.Integer, db.ForeignKey('hipe.id')),
        db.Column('score', db.Integer)
        )


def random_hipe():
    return Hipe.query.order_by(func.random()).first()


class User(UserMixin,db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    display_name = db.Column(db.String(64))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    followed = db.relationship('User',
            secondary = followers,
            primaryjoin = (followers.c.follower_id == id),
            secondaryjoin = (followers.c.followed_id == id),
            backref = db.backref('followers', lazy = 'dynamic'),
            lazy='dynamic')

    solved = db.relationship('Hipe',
            secondary = solvers,
            backref = 'solvers',
            lazy = 'dynamic'
            )


    def get_id(self):
        try:
            return unicode(self.id)  #python 2
        except NameError:
            return str(self.id)

    @staticmethod
    def make_unique_username(username):
        if User.query.filter_by(username=username).first() is None:
            return username
        version = 2
        while True:
            new_username = username + str(version)
            if User.query.filter_by(username=new_username).first() is None:
                break
            version +=1
        return new_username

    def solve(self, hipe):
        if not self.has_solved(hipe):
            self.solved.append(hipe)
        return self

    
    def has_solved(self, hipe):
        return self.solved.filter(solvers.c.hipe_id == hipe.id).count()

    def solved_hipes(self):
        return Hipe.query.join(solvers, (solvers.c.hipe_id == Hipe.id)).filter(solvers.c.solver_id == self.id)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self,user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self,user):
        return self.followed.filter(followers.c.followed_id == user.id).count()


    def __repr__(self):
        return '<User %r>' %(self.username)


class Hipe(db.Model):
    __tablename__ = 'hipe'
    id = db.Column(db.Integer, primary_key= True)
    letters = db.Column(db.String(4))
    answers = db.relationship('Answer', backref = 'hipe', lazy = 'dynamic')

    def __init__(self, letters):
        self.letters = letters


    
class Answer(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    answer = db.Column(db.String(20))
    hipe_id = db.Column(db.Integer, db.ForeignKey('hipe.id'))

    def __init__(self, word):
        self.answer = word

