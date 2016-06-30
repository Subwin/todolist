from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import abort
from flask import session
from flask import flash

import json

from models import TodoList
from models import User
from models import Comment

from mylog import log

app = Flask(__name__)
app.secret_key = 'subwin'


def current_user():
    user_id = session['user_id']
    log('debug user_id =', user_id)
    user = User.query.filter_by(id=user_id).first()
    log('debug user =', user)
    return user


@app.route('/')
def index():
    return redirect(url_for('login_view'))


@app.route('/login')
def login_view():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    # request.get_data()可以得到原始的请求语句
    form = request.get_json()
    print('debug form', form)
    login_u = User(form)
    data_u = User.query.filter_by(username=login_u.username).first()
    status = {
        'result': '',
        'url':'',
    }
    if data_u is None:
        # flash('登录失败')
        status['result'] = '登录失败'
        r = json.dumps(status, ensure_ascii=False)
        log('用户登录失败', login_u)
        return r

    if data_u.login_validator(login_u):
        log('用户登录成功')
        session['user_id'] = data_u.id
        if data_u.is_admin():
            # r = redirect(url_for('admin_view'))
            # return r
            status['result'] = '登陆成功'
            status['url'] = url_for('admin_view')
            log('status["url"]', status['url'])
            r = json.dumps(status, ensure_ascii=False)
            return r
        else:
            status['result'] = '登陆成功'
            status['url'] = url_for('todo_add_view', username=data_u.username)
            log('status["url"]', status['url'])
            r = json.dumps(status, ensure_ascii=False)
            return r
    else:
        status['result'] = '登录失败'
        r = json.dumps(status, ensure_ascii=False)
        log('用户登录失败', login_u)
        return r


@app.route('/timeline/<username>')
def timeline_view(username):
    t_user = User.query.filter_by(username=username).first()
    todo_list = t_user.todolists
    return render_template('timeline.html', todolists = todo_list, user=current_user(), t_user=t_user)


@app.route('/register', methods=['POST'])
def register():
    form = request.get_json()
    log('debug form = ', form)
    status = {
        'result':'',
        'url':'',
    }
    u = User(form)
    if u.regist_validator():
        u.save()
        # save了之后才进入数据库，才有id
        session['user_id'] = u.id
        log('debug session[user_id] =', session['user_id'])
        log('debug u.id =', u.id)
        status['result'] = '注册成功'
        status['url'] = url_for('todo_add_view', username=u.username)
        r = json.dumps(status, ensure_ascii=False)
        return r
    else:
        # flash('注册失败')
        status['result'] = '注册失败'
        log('注册失败', form)
        r = json.dumps(status, ensure_ascii=False)
        return r


@app.route('/todo/admin')
def admin_view():
    user_list = User.query.all()
    return render_template('admin.html', users=user_list, user = current_user())


@app.route('/todo/add/<username>')
def todo_add_view(username):
    data_u = User.query.filter_by(username=username).first()
    cur_u = current_user()
    if data_u is None:
        abort(404)
    elif data_u != cur_u and not cur_u.is_admin():
        todo_list = cur_u.todolists
        todo_list.sort(key=lambda t: t.created_time, reverse=True)
        return redirect(url_for('todo_add_view', username=cur_u.username))
        # abort(401)
    else:
        todo_list = data_u.todolists
        todo_list.sort(key=lambda t: t.created_time, reverse=True)
        all_todo_list = TodoList.query.all()
        all_todo_list.sort(key=lambda t: t.created_time, reverse=True)
        #要排序肯定要拿出每个元素传入sort，t就是每个元素
        return render_template('todo_list_add.html', todo_list=todo_list, user=data_u, all_todo_list=all_todo_list)


@app.route('/todo/add/<username>', methods=['POST'])
def todo_add(username):
    user = User.query.filter_by(username=username).first()
    # log('user= ', user.id, user.username)
    form = request.form
    # log('form= ', form)
    one_todo = TodoList(form)
    one_todo.user = user
    # log('one_todo= ', one_todo.id, one_todo.content, one_todo.user_id)
    one_todo.save()

    return redirect(url_for('todo_add_view', username=username))


@app.route('/todo/update/<todo_id>')
def todo_update_view(todo_id):
    one_todo = TodoList.query.filter_by(id=todo_id).first()
    return render_template('todo_list_update.html', todo=one_todo, user = current_user())


@app.route('/todo/update/<todo_id>', methods=['POST'])
def todo_update(todo_id):
    user = TodoList.query.filter_by(id=todo_id).first().user
    form = request.form
    one_todo = TodoList.query.filter_by(id=todo_id).first()
    one_todo.update(form)
    one_todo.save()
    return redirect(url_for('todo_add_view', username=user.username))


@app.route('/todo/delete/<todo_id>')
def todo_delete(todo_id):
    user = TodoList.query.filter_by(id=todo_id).first().user
    one_todo = TodoList.query.filter_by(id=todo_id).first()
    one_todo.delete()
    return redirect(url_for('todo_add_view', username=user.username))


@app.route('/timeline/comments/<todo_id>')
def comment_view(todo_id):
    todo = TodoList.query.filter_by(id=todo_id).first()
    comments = todo.comments
    log('debug comments = ', comments)
    comments.sort(key=lambda t:t.created_time, reverse=True)
    return render_template('comment.html', comments = comments, todo=todo, user = current_user())


@app.route('/timeline/comments/<todo_id>', methods=["POST"])
def comment(todo_id):
    comment_user = current_user()
    form = request.form
    one_comment = Comment(form)
    one_comment.user = comment_user
    one_comment.todolist = TodoList.query.filter_by(id=todo_id).first()
    #有外键记得把每个外键连上
    one_comment.save()
    return redirect(url_for('comment_view', todo_id = todo_id))


if __name__ == '__main__':
    # host, port = '0.0.0.0', 19000
    # args = {
    #     'host': host,
    #     'port': port,
    #     'debug': True,
    # }
    # app.run(**args)
    app.run(debug=True)