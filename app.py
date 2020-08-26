from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename

local_server = True
with open('config.json','r') as c:
    params = json.load(c)['params']

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)

mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(80), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    by = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(25), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    image = db.Column(db.Text, nullable=False)

@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    return render_template("index.html", params=params, posts=posts)

@app.route('/post/<string:post_slug>', methods = ["GET"])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("single.html",params=params, post=post)

@app.route('/about')
def about():
    return render_template("about.html",params=params)

@app.route('/login', methods=["GET","POST"])
def login():

    if 'user' in session and session['user'] == params['admin-user']:
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)


    if request.method =="POST":
        uname = request.form.get("uname")
        password = request.form.get("password")

        if(uname == params['admin-user'] and password == params['admin-password']):
            session['user'] = uname
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
    else:
        return render_template("login.html",params=params)


@app.route('/uploader', methods=["GET","POST"])
def uploader():
    if 'user' in session and session['user'] == params['admin-user']:
        if request.method=="POST":
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return "Upload Successful"



@app.route('/logout')
def logout():
    session.pop('user')
    return redirect("/login")
    
@app.route('/delete/<string:sno>', methods = ["GET", "POST"])
def delete(sno):
    if 'user' in session and session['user'] == params['admin-user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/login")

@app.route('/edit/<string:sno>', methods = ["GET", "POST"])
def edit(sno):
    if 'user' in session and session['user'] == params['admin-user']:
        if request.method =="POST":
            req_title = request.form.get("title")
            author = request.form.get("author")
            category = request.form.get("category")
            slug = request.form.get("slug")
            content = request.form.get("content")
            pic = request.files["file2"]
            date = datetime.now()

            if sno == '0':
                post = Posts(title=req_title, slug=slug, content=content, category=category, by=author, image=pic.read(), date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = req_title
                post.slug = slug
                post.content = content
                post.category = category 
                post.date = date 
                post.by = author
                post.image = image
                db.session.commit()
                return redirect('/edit/'+ sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post = post, sno=sno)

@app.route('/category')
def category():
    return render_template("category.html",params=params)

@app.route('/contact', methods = ['GET','POST'])
def contact():

    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        phone = request.form.get("phn")
        message = request.form.get("message")

        entry = Contact(firstname=fname, lastname=lname, email=email, phone=phone, message=message)
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from ' + fname + " " + lname,
        #                 sender=email,
        #                 recipients = [params['gmail-user']],
        #                 body = message +'\n' + phone
        #                 )


    return render_template("contact.html",params=params)

app.run(debug=True)