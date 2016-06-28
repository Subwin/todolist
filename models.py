from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import sql
import hashlib
import time
import shutil

db_path = 'db.sqlite'
app = Flask(__name__)
app.secret_key = 'random string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    password = db.Column(db.String())
    role = db.Column(db.Integer, default = 2)
    created_time = db.Column(db.DateTime(timezone=True),
                             default=sql.func.now())
    todolists = db.relationship('TodoList', backref='user')
    comments = db.relationship('Comment', backref='user')
    def __init__(self, form):
        super(User, self).__init__()
        self.username = form['username']
        self.password = hash_sha1(form['password'])

    def __repr__(self):
        class_name = self.__class__.__name__
        return u'<{}: {}>'.format(class_name, self.id)

    def is_admin(self):
        return self.role == 1

    def update(self, form):
        print('user.update, ', form)
        new_password = form['password'] if form['password'] != '' else self.password
        self.content = new_password

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def regist_validator(self):
        user_list =[u.username for u in User.query.all()]
        username_len = len(self.username) >= 3
        password_len = len(self.password) >= 3
        registed = self.username not in user_list
        return username_len and password_len and registed

    def login_validator(self, user):
        if isinstance(user, User):
            username_equals = self.username == user.username
            password_equals = self.password == user.password
            return username_equals and password_equals
        else:
            return False


class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    created_time = db.Column(db.DateTime(timezone=True),
                             default=sql.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref="todolist")

    def __init__(self, form):
        super(TodoList, self).__init__()
        self.content = form['content']

    def __repr__(self):
        class_name = self.__class__.__name__
        return u'<{}: {}>'.format(class_name, self.id)

    def update(self, form):
        print('todo.update, ', form)
        new_content = form['content'] if form['content'] != '' else self.content
        self.content = new_content

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    created_time = db.Column(db.DateTime(timezone=True),
                             default=sql.func.now())
    post_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_todolist_id =  db.Column(db.Integer, db.ForeignKey('todolists.id'))

    def __init__(self, form):
        super(Comment, self).__init__()
        self.content = form['content']

    def __repr__(self):
        class_name = self.__class__.__name__
        return u'<{}: {}>'.format(class_name, self.id)

    def update(self, form):
        print('comment.update, ', form)
        new_content = form['content'] if form['content'] != '' else self.content
        self.content = new_content

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


def hash_sha1(password):
    password = password.encode('utf-8')
    sha1 = hashlib.sha1()
    sha1.update(password)
    return sha1.hexdigest()


def backup_db():
    backup_path = '{}.{}'.format(time.time(), db_path)
    shutil.copyfile(db_path, backup_path)


def rebuild_db():
    backup_db()
    db.drop_all()
    db.create_all()
    print('rebuild database')


if __name__ == '__main__':
    rebuild_db()