
from flask import Flask, redirect, url_for, request, jsonify, render_template, flash, session
from firebase_admin import credentials, firestore, initialize_app
from flask_wtf import Form
import re
from requests import Response
import pdfkit
import uuid
import datetime
from functools import wraps
from configFile import *
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, DateField
from datetime import datetime, date
import pyrebase
import os
app = Flask(__name__)
cred = credentials.Certificate('key.json')


default_app = initialize_app(cred)
db = firestore.client()
firebase = pyrebase.initialize_app(config)
db1 = firebase.database()
storage = firebase.storage()
events = db.collection('Events')
UpcomingEvents = db.collection('UpcomingEvents')
auth = firebase.auth()


def is_logged_in(f):
    # Have to figure out what the heck does this wraps do!!
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect('/admin')
    return wrap


def is_not_logged_in(f):
    # Have to figure out what the heck does this wraps do!!
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return redirect('/dashboard')
        else:
            return f(*args, **kwargs)
    return wrap


@app.route('/')
def index():
    upcomingEvents = db.collection('UpcomingEvents').order_by(
        u'date', direction=firestore.Query.DESCENDING).limit(3).stream()
    upcomingArr = []
    for doc in upcomingEvents:
        today = date.today()
        d1 = today.strftime("%d/%m/%Y")
        d1 = d1[6:10]
        print(d1)
        upcomingArr.append(doc.to_dict())
        print(doc.to_dict())
    return render_template('index.html', upcomingEvents=upcomingArr, d1=d1)


@app.route('/team')
def team():
    return render_template('team.html')


# @app.route('/events2019')
# def events2019():


class ArticleForm(Form):

    title = StringField('Title', [validators.length(min=1, max=50)])
    body = TextAreaField('Body', [validators.length(min=30)])
    image_url = StringField(
        'ImageUrl', [validators.URL(require_tld=False, message=None)])
    venue = StringField('Venue', [validators.length(min=5, max=50)])
    time = StringField('Time', [validators.length(min=2, max=10)])
    date = DateField('Date', format='%Y-%m-%d')


class UpcomingForm(Form):

    title = StringField('Title', [validators.length(min=1, max=50)])
    image_url = StringField(
        'ImageUrl', [validators.URL(require_tld=False, message=None)])
    venue = StringField('Venue', [validators.length(min=5, max=50)])
    time = StringField('Time', [validators.length(min=2, max=10)])
    date = DateField('Date', format='%Y-%m-%d')
    level = StringField('Level', [validators.length(min=5, max=15)])
    event_url = StringField(
        'EventUrl', [validators.URL(require_tld=False, message=None)])


class Blog(Form):

    title = StringField('Title', [validators.length(min=1, max=50)])
    imageName = StringField('Name', [validators.length(min=1, max=150)])
    subtitle = StringField('SubTitle', [validators.length(min=1, max=150)])
    date = DateField('Date', format='%Y-%m-%d')
    author = StringField('Author', [validators.length(min=1, max=50)])
    topic = StringField('Topic', [validators.length(min=1, max=50)])
    content = TextAreaField('BlogContent', [validators.length(min=30)])
    imageUrl = StringField(
        'ImageUrl', [validators.URL(require_tld=False, message=None)])


# Blog Page
@app.route('/blogs')
def blogs():
    blogs = db.collection('blogs').order_by(
        u'timestamp', direction=firestore.Query.DESCENDING).get()
    blogsArr = []
    for blog in blogs:
        blogsArr.append(blog.to_dict())
    headArr = blogsArr
    headArr = headArr[:3]
    return render_template('blogs.html', blogs=blogsArr, headArr=headArr)


# Blog Post
@app.route('/blog_post/<string:post_id>', methods=['GET'])
def post(post_id):
    posts = db.collection('blogs').where("id", "==", post_id).get()
    postArr = []
    for post in posts:
        postArr.append(post.to_dict())

    return render_template('blog_post.html', post=postArr)

# Add blog post


@app.route('/add_blog_post', methods=['POST', 'GET'])
@is_logged_in
def addPost():
    form = Blog(request.form)
    if request.method == 'POST':
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y--%H:%M:%S")

        title = form.title.data
        subtitle = form.subtitle.data
        author = form.author.data
        blogContent = form.content.data
        image = form.imageUrl.data
        topic = form.topic.data
        dateTime = datetime.now()
        id1 = str(uuid.uuid4())

        data = {"id": id1, 'title': title, 'subtitle': subtitle, "image": image, "topic": topic,
                'author': author, 'blogContent': blogContent, 'date': dateTime.strftime("%m/%d/%Y"), "timestamp": timestamp}
        db.collection('blogs').document(id1).set(data)
        return redirect('/blogs')
    else:
        return render_template('add_blog_post.html', form=form)

# Edit Blog post


@app.route('/edit_blog_post/<string:post_id>', methods=['GET', 'POST'])
@is_logged_in
def editPost(post_id):
    if request.method == 'GET':
        posts = db.collection('blogs').where("id", "==", post_id).get()
        postArr = []
        for post in posts:
            postArr.append(post.to_dict())
        return render_template('edit_blog_post.html', post=postArr)
    else:
        form = Blog(request.form)
    if request.method == 'POST':
        title = form.title.data
        subtitle = form.subtitle.data
        author = form.author.data
        blogContent = form.content.data
        image = form.imageUrl.data
        topic = form.topic.data

        data = {'title': title, 'subtitle': subtitle, "image": image,
                'author': author, 'blogContent': blogContent, "topic": topic}
        db.collection('blogs').document(post_id).update(data)
        return redirect('/dashboard')


# Delete blog Post

@app.route('/delete_blog/<string:id>', methods=['POST'])
@is_logged_in
def delete_blog(id):
    try:
        db.collection(u'blogs').document(id).delete()
        return redirect(url_for('dashboard'))
    except:
        flash('Some error occured', 'danger')


# This route is regarding the event posting.


@app.route('/add_article', methods=['POST', 'GET'])
@is_logged_in
def postEvent():
    form = ArticleForm(request.form)
    if request.method == 'POST':
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y--%H:%M:%S")

        title = form.title.data
        body = form.body.data
        image_url = form.image_url.data
        venue = form.venue.data
        date = str(form.date.data)
        time = str(form.time.data)
        idparam1 = title.replace(" ", "")
        id1 = idparam1+"-"+date
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            'cookie': [
                ('cookie-name1', 'cookie-value1'),
                ('cookie-name2', 'cookie-value2'),
            ],
            'no-outline': None
        }

        try:
            pdfkit.from_string(body, 'genReport.pdf')
            pdfkit.from_string(body, 'genReport.docx')
            report = str(title)+"-"+str(date)
            storage.child('reportsPdf/{}'.format(report)).put('genReport.pdf')
            storage.child('reportsDocx/{}'.format(report)
                          ).put('genReport.docx')
            pdf_url = storage.child(
                'reportsPdf/{}'.format(report)).get_url(None)
            docx_url = storage.child(
                'reportsDocx/{}'.format(report)).get_url(None)
        except:
            pdf_url = ""
            docx_url = ""
        print(pdf_url)
        eventData = {
            "title": title,
            "date": date,
            "id": id1,
            "timestamp": timestamp,
            "time": time,
            "image_url": image_url,
            "venue": venue,
            "body": body,
            "pdf_url": pdf_url,
            "docx_url": docx_url
        }

        res = events.document(timestamp).set(eventData)
        data = {
            "message": "event_added",
            "timestamp": timestamp
        }
        return redirect('/dashboard')
    elif request.method == 'GET':
        return render_template('add_article.html', form=form)
    else:
        return "Invalid request"


@app.route('/add_upcoming_event', methods=['POST', 'GET'])
@is_logged_in
def postUpcomingEvent():
    form = UpcomingForm(request.form)
    if request.method == 'POST':
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y--%H:%M:%S")

        title = form.title.data
        image_url = form.image_url.data
        event_url = form.event_url.data
        venue = form.venue.data
        level = form.level.data
        date = str(form.date.data)
        time = str(form.time.data)
        idparam1 = title.replace(" ", "")
        id1 = idparam1+"-"+date

        eventData = {
            "title": title,
            "date": date,
            "id": id1,
            "timestamp": timestamp,
            "time": time,
            "level": level,
            "image_url": image_url,
            "venue": venue,
            "event_url": event_url
        }
        res = UpcomingEvents.document(timestamp).set(eventData)
        data = {
            "message": "upcoming_event_added",
            "timestamp": timestamp
        }
        return redirect('/dashboard')
    elif request.method == 'GET':
        return render_template('add_upcoming_event.html', form=form)
    else:
        return "Invalid request"


@app.route('/admin', methods=['GET', 'POST'])
@is_not_logged_in
def login():
    if request.method == 'POST':

        # Get for fields.
        username = request.form['username']
        password = request.form['password']
        try:
            auth.sign_in_with_email_and_password(username, password)
            flash('Login Successful')
            session['logged_in'] = True
            session['username'] = username
            return redirect('/dashboard')

        except:
            flash('Please check your credentials')
            return redirect('/admin')
    # The below goes if it is a get request.
    return render_template('login.html')


# The below route will check if logged in


@app.route('/logout')
@is_logged_in
def logout():
    # We just have to clear the session, this will automatically set it to false.
    session.clear()
    return redirect('/admin')


@app.route('/dashboard')
# Allowed only if logged in.
@is_logged_in
def dashboard():
    blogs = db.collection('blogs').order_by(
        u'timestamp', direction=firestore.Query.DESCENDING).get()
    blogsArr = []
    for blog in blogs:
        blogsArr.append(blog.to_dict())
    docs = db.collection('Events').order_by(
        u'date', direction=firestore.Query.DESCENDING).stream()
    # I want to automate event deletion too, but i don;t want to as i am very tired
    upcomingEvents = db.collection('UpcomingEvents').order_by(
        u'date', direction=firestore.Query.DESCENDING).limit(3).stream()
    docsArr = []
    for doc in docs:
        docsArr.append(doc.to_dict())
    upcomingArr = []
    for doc in upcomingEvents:
        upcomingArr.append(doc.to_dict())
        print(doc.to_dict())
    return render_template('dashboard.html', docs=docsArr, upcoming=upcomingArr, blogs=blogsArr)


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    try:
        db.collection(u'Events').document(id).delete()
        return redirect(url_for('dashboard'))
    except:
        flash('Some error occured', 'danger')


# Upcoming Article deletion done
@app.route('/delete_upcoming_event/<string:id>', methods=['POST'])
@is_logged_in
def delete_upcoming_event(id):
    try:
        db.collection(u'UpcomingEvents').document(id).delete()
        return redirect(url_for('dashboard'))
    except:
        flash('Some error occured')

# Now, this route will get the acticles of 2019.


@app.route('/articles_filter/<string:year>/')
def articles_year(year):
    all_posts = [doc.to_dict() for doc in events.order_by(
        u'date', direction=firestore.Query.DESCENDING).stream()]
    post_2017 = []
    post_2018 = []
    post_2019 = []
    post_2020 = []
    post_2021 = []
    post_2022 = []

    for post in all_posts:
        if("2017" in post['date']):
            post_2017.append(post)
        elif("2018" in post['date']):
            post_2018.append(post)
        elif("2019" in post['date']):
            post_2019.append(post)
        elif("2020" in post['date']):
            post_2020.append(post)
        elif("2021" in post['date']):
            post_2021.append(post)
        elif("2022" in post['date']):
            post_2022.append(post)
        else:
            # This should be handled, when the website will be again up for maintenance.
            print("Maintenance required")
    if(year == "2017"):
        eventsData = post_2017
    elif(year == "2018"):
        eventsData = post_2018
    elif(year == "2019"):
        eventsData = post_2019
    elif(year == "2020"):
        eventsData = post_2020
    elif(year == "2021"):
        eventsData = post_2021
    elif(year == "2022"):
        eventsData = post_2022
    else:
        print("Maintenance required")
        eventsData = jsonify([{}])

    return render_template('articles.html', events=eventsData, year=year)


# This is for opening up a specific artcile.
@app.route('/article/<string:year>/<string:id1>')
def article1(year, id1):
    all_posts = [doc.to_dict() for doc in events.stream()]
    post_2017 = []
    post_2018 = []
    post_2019 = []
    post_2020 = []
    post_2021 = []
    post_2022 = []

    for post in all_posts:
        if("2017" in post['date']):
            post_2017.append(post)
        elif("2018" in post['date']):
            post_2018.append(post)
        elif("2019" in post['date']):
            post_2019.append(post)
        elif("2020" in post['date']):
            post_2020.append(post)
        elif("2021" in post['date']):
            post_2021.append(post)
        elif("2022" in post['date']):
            post_2022.append(post)
        else:
            # This should be handled, when the website will be again up for maintenance.
            print("Maintenance required")
    if(year == "2017"):
        eventsData = post_2017
    elif(year == "2018"):
        eventsData = post_2018
    elif(year == "2019"):
        eventsData = post_2019
    elif(year == "2020"):
        eventsData = post_2020
    elif(year == "2021"):
        eventsData = post_2021
    elif(year == "2022"):
        eventsData = post_2022
    else:
        print("Maintenance required")
        eventsData = jsonify([{}])
    for event in eventsData:
        print(event)
        if str(event['id']) == str(id1):
            sendEvent = event
            break
    # return "Hello world"
    return render_template('article.html', event=sendEvent)


@app.route('/edit_post/<string:id>/<string:timestamp>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id, timestamp):

    form = ArticleForm(request.form)
    # Gets what the user edited basically.

    article = db.collection(u'Events').document(timestamp).get()
    article = article.to_dict()
    if request.method == 'GET':
        form.title.data = article['title']
        form.body.data = article['body']
        form.image_url.data = article['image_url']
        form.venue.data = article['venue']

    if request.method == 'POST':

        title = form.title.data
        body = form.body.data
        image_url = form.image_url.data
        venue = form.venue.data
        idparam1 = title.replace(" ", "")
        date = article['date']
        time = article['time']
        id1 = idparam1+"-"+date

        print(body)

        try:
            pdfkit.from_string(body, 'genReport.pdf')
            pdfkit.from_string(body, 'genReport.docx')
            report = str(title)+"-"+str(date)
            storage.child('reportsPdf/{}'.format(report)).put('genReport.pdf')
            storage.child('reportsDocx/{}'.format(report)
                          ).put('genReport.docx')
            pdf_url = storage.child(
                'reportsPdf/{}'.format(report)).get_url(None)
            docx_url = storage.child(
                'reportsDocx/{}'.format(report)).get_url(None)
        except:
            pdf_url = ""
            docx_url = ""

        eventData = {
            "title": title,
            "date": date,
            "id": id1,
            "timestamp": timestamp,
            "time": time,
            "image_url": image_url,
            "venue": venue,
            "body": body,
            "pdf_url": pdf_url,
            "docx_url": docx_url
        }

        res = events.document(timestamp).set(eventData)
        data = {
            "message": "event_updated(This will return previous timestamp only",
            "timestamp": timestamp
        }
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'GET':
        return render_template('upload.html')
    else:
        images = request.files
        details = request.form.to_dict()
        name = details['event-name']
        date = details['event-date']

        images = images.getlist('images')

        links = []

        for i in range(len(images)):
            image_name = str(images[i]).split()[1].strip("'")
            print("Uploading image %d" % i)
            storage.child('images/{}'.format(name + "/" +
                                             image_name)).put(images[i])
            links.append(storage.child(
                'images/{}'.format(name + "/" + image_name)).get_url(None))
        json = {'urls': tuple(i for i in links)}
        urlArr = [i for i in links]
        db1.child('image_urls').child(name + " " + date).set(urlArr)

        return redirect('/dashboard')


@app.route('/gallery', methods=['GET'])
def showImages():
    allData = db1.child('image_urls').get().val()
    eventUrls = []
    eventName = []
    eventDate = []
    for event, urls in allData.items():
        x = len(event)
        eventName.append(event[:-10])
        eventDate.append(event[-10:])
        eventUrls.append(urls)
        print(urls)
    return render_template('gallery.html', eventDate=eventDate, eventName=eventName, eventUrls=eventUrls)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        today = date.today()
        d1 = today.strftime("%d/%m/%Y")
        d1 = d1[6:10]
        return render_template('search.html')
    else:
        today = date.today()
        d1 = today.strftime("%d/%m/%Y")
        d1 = d1[6:10]
        name = request.form['search']
        name = name.replace(" ", "")
        name = name.lower()
        eventsData1 = db.collection(u'Events').stream()
        eventArr = []
        titleArr = []
        for event in eventsData1:
            temp = event.to_dict()
            eventArr.append(temp)
            titleArr.append(temp['title'].replace(" ", "").lower())

        docValues = []
        searchValues = []
        yearValues = []
        for i in range(0, len(titleArr)):
            if name in titleArr[i]:
                docValues.append(i)
                searchValues.append(eventArr[i])
                yearValues.append(eventArr[i]['date'][0:4])
        print(yearValues)
        values = zip(searchValues, yearValues)
    return render_template('search.html', searchValues=searchValues, eventValues=values, d1=d1)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


app.config['SECRET_KEY'] = 'dscrit'

if __name__ == '__main__':
    app.run(debug=True)
