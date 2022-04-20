import flask
import pymysql

from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import json
from datetime import datetime
import math

pymysql.install_as_MySQLdb()

with open('config.json', 'r') as c:
    params = json.load(c)["params"]
local_server = True
app = Flask(__name__)
app.secret_key = 'abra-ca-dabra'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL='True',
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    # [0:params['no_of_posts']]
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev,
                           next=next)  # first params will be used in html to display
    # using jinja.
    # 2nd params is from the python program


@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user' in session and session['user'] == params['admin_user']:  # check if user is logged in
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            session['user'] = username  # session is a dictionary
            posts = Posts.query.all()
            params['login_panel'] = "Dashboard"
            return render_template('dashboard.html', params=params, posts=posts)
    return render_template('login.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            box_tagline = request.form.get('tagline')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')

            if sno == '0':
                post = Posts(title=box_title, tagline=box_tagline, slug=box_slug, content=box_content,
                             date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = box_tagline
                post.slug = box_slug
                post.content = box_content
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # add value to database
        name2 = request.form.get('name')
        email2 = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name2, email=email2, phone_num=phone, msg=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name2, sender=email2,
                          recipients=[params['gmail-user']],
                          body=message + "\n" + phone
                          )
    return render_template('contact.html', params=params)


@app.route('/logout')
def logout():
    session.pop('user', None)
    params['login_panel'] = "Login"
    return redirect('/login')


@app.route('/delete/<string:sno>', methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')


# @app.route("/post")
# def post_direct():
#     return render_template('post.html', params=params)


app.run(debug=True)
