    
from flask import Flask, redirect, url_for,request,jsonify,render_template,flash,session;
from firebase_admin import credentials, firestore, initialize_app;
from flask_wtf import Form
import uuid
from functools import wraps
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,DateField;
from datetime import datetime
import pyrebase
app = Flask(__name__)
cred = credentials.Certificate('key.json')


config = {
    "apiKey": "AIzaSyCleol3wnsu7Jpe-UM2AX3zhBCP0JAAMm0",
    "authDomain": "dsc-website-debbf.firebaseapp.com",
    "databaseURL": "https://dsc-website-debbf.firebaseio.com",
    "projectId": "dsc-website-debbf",
    "storageBucket": "dsc-website-debbf.appspot.com",
    "messagingSenderId": "161083743915",
    "appId": "1:161083743915:web:4e0e83c8b48638248261ee"
}

default_app = initialize_app(cred)
db = firestore.client()
firebase = pyrebase.initialize_app(config)
events  = db.collection('Events')
auth = firebase.auth()

def is_logged_in(f):
    #Have to figure out what the heck does this wraps do!!
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login','danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/team')
def team():
    return render_template('team.html')

# Event Page
@app.route('/event')
def event():
    return render_template('event.html')

# Events Page
@app.route('/events')
def events():
    return render_template('events.html')

class ArticleForm(Form):

    title = StringField('Title',[validators.length(min=1,max=50)])
    body = TextAreaField('Body',[validators.length(min=30)])
    image_url = StringField('ImageUrl',[validators.URL(require_tld=False,message=None)])
    venue = StringField('Venue',[validators.length(min=5,max=50)])
    time = StringField('Time',[validators.length(min=2,max=10)])
    date = DateField('Date', format='%Y-%m-%d') 


# This route is regarding the event posting.
@app.route('/post-event',methods=['POST','GET'])
@is_logged_in
def postEvent():
    form  = ArticleForm(request.form)
    if request.method == 'POST':
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y--%H:%M:%S")

        title = form.title.data
        body = form.body.data
        image_url = form.image_url.data
        venue = form.venue.data
        date = str(form.date.data)
        time = str(form.time.data)
        idparam1 = title.replace(" ","")
        id1 = idparam1+"-"+date
        eventData = {
            "title":title,
            "date":date,
            "id":id1,
            "time":time,
            "image_url":image_url,
            "venue":venue,
            "body":body
        }
        
        res = events.document(timestamp).set(eventData)

        data = {
            "message":"event_added",
            "timestamp": timestamp
        }
        return data
    elif request.method == 'GET':
        return render_template('add_article.html',form=form)
    else:
        return "Invalid request"

#This route will be regarding user sign in

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':

        #Get for fields.
        username = request.form['username']
        password= request.form['password']
        try:
            auth.sign_in_with_email_and_password(username,password)
            flash('Login Successful','success')
            session['logged_in'] = True
            session['username'] = username
            return render_template('add_article.html')
            
        except:
            flash('Please check your credentials')

    #The below goes if it is a get request.
    return render_template('login.html')





#The below route will check if logged in


@app.route('/logout')
@is_logged_in
def logout():
    session.clear() #We just have to clear the session, this will automatically set it to false.
    flash('You are now logged out','success')
    return "Hello world"



#Now, this route will get the acticles of 2019.
@app.route('/articles_filter/<string:year>/')
def articles_year(year):
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
            #This should be handled, when the website will be again up for maintenance.
            print("Maintenance required")
    if(year == "2017"):
        eventsData =  post_2017
    elif(year == "2018"):
        eventsData =  post_2018
    elif(year == "2019"):
        eventsData =  post_2019
    elif(year == "2020"):
        eventsData =  post_2020
    elif(year == "2021"):
        eventsData =  post_2021
    elif(year == "2022"):
        eventsData =  post_2022   
    else:
        print("Maintenance required")     
        eventsData = jsonify([{}])

    return render_template('articles.html',events=eventsData,year=year)
        

#This is for opening up a specific artcile.
@app.route('/article/<string:year>/<string:id1>')
def article1(year,id1):
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
            #This should be handled, when the website will be again up for maintenance.
            print("Maintenance required")
    if(year == "2017"):
        eventsData =  post_2017
    elif(year == "2018"):
        eventsData =  post_2018
    elif(year == "2019"):
        eventsData =  post_2019
    elif(year == "2020"):
        eventsData =  post_2020
    elif(year == "2021"):
        eventsData =  post_2021
    elif(year == "2022"):
        eventsData =  post_2022   
    else:
        print("Maintenance required")     
        eventsData = jsonify([{}])
    for event in eventsData:
        print(event)
        if str(event['id']) == str(id1):
            sendEvent = event
            break
    # return "Hello world"
    return render_template('article.html',event=sendEvent)


if __name__ == '__main__':
    app.secret_key = 'secret_123'
    app.run(debug=True)
