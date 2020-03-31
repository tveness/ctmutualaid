#!/usr/bin/env python

from flask import Flask, request, abort, jsonify, Response, render_template, url_for, redirect, flash
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user, logout_user
from flaskext.markdown import Markdown
from validate_email import validate_email

import config

import re
import sqlite3
import string
import json
import bcrypt
import secrets


#prefix="api"
USER_DB_PATH=config.USER_DB_PATH
DB_PATH=config.DB_PATH


app = Flask(__name__)
login_manager=LoginManager(app)
login_manager.session_protection=None
Markdown(app)
app.config['SECRET_KEY']=config.secret_key
#app.config['SERVER_NAME']='ctmutualaid.com'
#app.config['SESSION_COOKIE_DOMAIN']='ctmutualaid.com'

def add_user(user,password,email):
    #Generate activation url token
    active=secrets.token_urlsafe(16)

    #Salt and hash password with bcrypt
    salt=bcrypt.gensalt()
    hashed=bcrypt.hashpw(password.encode(),salt)

    #Add data to database
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("INSERT into credentials (username, hashed_pw, email, active) VALUES (?,?,?,?)",(user,hashed,email,active))
    conn.commit()

    conn.close()
    return user

@app.route('/add-user',methods=['GET','POST'])
def add_user_page():
    if request.method == 'POST':
        #Validate user data
        if not validate_email(request.form['email']):
            flash("Invalid e-mail address", "warning")
            return redirect('/add-user')



        #Add user to database
        add_user(request.form['username'], request.form['password'], request.form['email'])

        flash("User added to system", "success")
        return redirect('/')
    if request.method == 'GET':
        content=get_page_vars('en')
        return render_template('add_user.html',content=content)

def get_unactivated_users():
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT username from credentials WHERE active!='True'")
    results=cursor.fetchall()
    conn.close()
    return results

def activate_user(user_id):
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("UPDATE credentials SET active='True' where username=?",(user_id,))
    conn.commit()
    conn.close()
    return user_id

def get_resource_list():
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT * from submitted_resources")
    results=cursor.fetchall()
    conn.close()
    return results

def get_category_list():
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT id,title from posts")
    results=cursor.fetchall()
    conn.close()
    d={}
    for i in results:
        d[i[0]]=i[1]
    return d

def remove_resource(resource_id):
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute("DELETE FROM submitted_resources where id=?",(resource_id,))
    conn.commit()
    conn.close()



@app.route('/view-resources',methods=['GET','POST'])
@login_required
def view_resources_page():
        if request.method=='POST':
            for i in request.form.getlist('toremove'):
                remove_resource(i)

            flash('Removed '+i,"success")
        resource_list=get_resource_list()
        content=get_page_vars('en')
        cat_list=get_category_list()
        return render_template('view-resources.html', content=content, resource_list=resource_list,cat_list=cat_list)



@app.route('/activate-user',methods=['GET','POST'])
@login_required
def active_user_page():
    if request.method == 'POST':
        #Add user to database
        user_name=activate_user(request.form['id'])
        flash("Activated user "+user_name, "success")
        return redirect('/')
    if request.method == 'GET':
        content=get_page_vars('en')
        user_list=get_unactivated_users()
        return render_template('activate_user.html',content=content,user_list=user_list)

def validate_credentials(username,password):
    #Connect to database, check is password is correct for particular user
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT hashed_pw,active from credentials WHERE username=?",(username,))
    results=cursor.fetchall()
    conn.close()
    if not results:
        return False

    hashed=results[0][0]
    if bcrypt.checkpw(password.encode(),hashed) and results[0][1]=='True':
        return True
    else:
        return False

def view_table(table_name):
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("PRAGMA table_info({})".format(table_name))
    r1=cursor.fetchall();
    r1=[i[1] for i in r1]
    cursor.execute("SELECT * from {}".format(table_name))
    r2=cursor.fetchall()
    conn.close()
    return [r1,r2]

def view_users():
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("PRAGMA table_info('credentials')")
    r1=cursor.fetchall();
    r1=[i[1] for i in r1]
    cursor.execute("SELECT username,email,active from 'credentials'")
    r2=cursor.fetchall()
    conn.close()
    return [r1,r2]

@app.route("/view-users",)
@login_required
def view_users_page():
    content=get_page_vars('en')
    coltitles,rows = view_users()
    return render_template("table-view.html", content=content,coltitles=['Username','E-mail','Active'],rows=rows,table_title='User view')

#@app.route('/user-list')
def get_users():
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT username from credentials")
    results=cursor.fetchall()
    conn.close()
    return [i[0] for i in results]

#User class for managing login
class User(UserMixin):
    user_database=get_users()
    def __init__(self,username):
        self.id=username
    @classmethod
    def get(cls,id):
        return cls.user_database.get(id)

@login_manager.user_loader
def load_user(userid):
    if userid in get_users():
        return User(userid)
    else:
        return None

#Redirect to English by default
#Make _all_ languages have a structure
#Can possibly update this to guess language based on user-agent data, and make
#it even more transparent for non-English users
@app.route("/")
def index(stuff=None):
    return redirect('/en/home')

@app.route("/a")
def a():
    return "a"

def validate_language(language):
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT * from languages where language=?",(language,))
    results=cursor.fetchall()
    conn.close()
    if len(results):
        return 1
    else:
        return 0







@app.route("/edit/<lang>/",methods=['POST','GET'])
@app.route("/edit/<lang>/<page>",methods=['POST','GET'])
@login_required
def edit_page(lang, page="home"):
    if request.method == 'POST':
        #update database
        conn=sqlite3.connect(DB_PATH)
        cursor=conn.cursor()
        results=cursor.fetchall()

        #get ids in the game
        ids={}
#        print([i for i in request.form.keys()])
        for i in request.form.keys():
            if(len(i.split('-',1))==2):
                id=int(i.split('-',1)[0])
                ids[id]=1



#        print(ids.keys())
        for id in ids.keys():
            title=request.form[str(id)+"-title"]
            content=request.form[str(id)+"-content"]
            cursor.execute("UPDATE posts SET title=?, content=? where id=?",(title,content,id))
        if "jumbo_title" in request.form.keys() and "jumbo_text" in request.form.keys():
            jumbo_title=request.form['jumbo_title']
            jumbo_text=request.form['jumbo_text']
            pj=page+"-jumbo"
            cursor.execute("UPDATE posts SET title=?, content=? where page_name=? and language=?",(jumbo_title,jumbo_text,pj,lang))


        conn.commit()
        conn.close()

        flash("Updated page", "success")
        return redirect('/'+lang+'/'+page)



    #First check language exists in the database
    if not validate_language(lang):
        abort(404)# "Language not implemented"
    #Check if page is in page list, otherwise throw error page for _that language_
    if page not in get_page_list(lang):
        abort(404)

    content=get_page_content(page,lang)

    return render_template("edit.html", content=content)



@app.route("/edit/",methods=["GET","POST"])
@login_required
def edit_master(lang, page="home"):
    return render_template("edit.html")


@app.route("/guess")
def guess():
    return "Done"

def get_page_content(page,lang):
    to_return={}
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()

    #Page list
    cursor.execute("SELECT page_name, display_name from pages where language=? AND visible='True'",(lang,))
    results=cursor.fetchall()
    to_return['pages']=results
    to_return['page']=page

    #Get page specific content
    cursor.execute("SELECT lead, page_content from pages WHERE page_name=? AND language=?",(page,lang))
    results=cursor.fetchall()
    to_return['lead'],to_return['page_content']=results[0]

    #Post list
    cursor.execute("SELECT * from posts where language=? AND page_name=?",(lang,page))
    results=cursor.fetchall()
    d={}
    for i in results:
        d[i[4]]=[i[0],i[3]]
    to_return['posts']=d

    #Site name
    cursor.execute("SELECT site_name, site_name_display, footer, rtl from languages WHERE language=?",(lang,))
    results=cursor.fetchall()
    to_return['site_name'], to_return['display_site_name'], to_return['footer'], to_return['rtl']=results[0]

    #Get languages
    cursor.execute("SELECT language,language_display from languages")
    to_return['langs']=cursor.fetchall()
    to_return['lang']=lang

    #Jumbotron?
    cursor.execute("SELECT * from posts where language=? AND page_name=?",(lang,page+"-jumbo"))
    results=cursor.fetchone()
    to_return['jumbo']=results


    conn.close()
    return to_return


def get_page_vars(lang):
    to_return={}
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()

    #Page list
    cursor.execute("SELECT page_name, display_name from pages where language=? AND visible='True'",(lang,))
    results=cursor.fetchall()
    to_return['pages']=results


    #Site name
    cursor.execute("SELECT site_name, site_name_display, footer, rtl from languages WHERE language=?",(lang,))
    results=cursor.fetchall()
    to_return['site_name'], to_return['display_site_name'], to_return['footer'], to_return['rtl']=results[0]

    #Get languages
    cursor.execute("SELECT language,language_display from languages")
    to_return['langs']=cursor.fetchall()

    conn.close()
    to_return['lang']=lang
    return to_return




def get_page_list(lang):
    to_return={}
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()

    #Page list
    cursor.execute("SELECT page_name from pages where language=?",(lang,))
    results=cursor.fetchall()
    return [i[0] for i in results]

def get_submit_content(lang):
    to_return={}
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()

    #Page list
    cursor.execute("SELECT * from submit_form where language=?",(lang,))
    results=cursor.fetchall()[0]
    conn.close()
    to_return['res_description']=json.loads(results[1])
    to_return['res_link']=json.loads(results[2])
    to_return['cats']=json.loads(results[3])
    to_return['submit_button']=results[4]
    return to_return
def get_categories(lang):
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()

    cursor.execute("SELECT id,title from posts WHERE language=? AND page_name=?",(lang,'links'))
    results=cursor.fetchall()
    conn.close()
    return results

def validate_form(submitted_form):
    return True

def insert_resource(submitted_form):
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()

    cursor.execute("INSERT into submitted_resources (resource_description,resource_link,category_id) VALUES (?,?,?)",(submitted_form['resource-text'],submitted_form['resource-link'],submitted_form['cat']))
    results=cursor.fetchall()
    conn.commit()
    conn.close()



@app.route("/<lang>/submit",methods=["GET","POST"])
def sub_page(lang):
    #Check page exists in language
    if 'submit' not in get_page_list(lang):
        abort(404)

    if request.method=="GET":
        form_content=get_submit_content(lang)
#        print(form_content)
        categories=get_categories(lang)
        content=get_page_vars(lang)
        content['page']='submit'
        return render_template('submit.html',form_content=form_content,categories=categories,showform=True,content=content)
    if request.method=="POST":
#        to_ret= request.form['sel1']+" "+request.form['resource-text']+request.form['resource-link']
        insert_resource(request.form)
        flash("Submitted successfully", "info")
        content=get_page_vars(lang)
        return render_template('submit.html', content=content)

@app.route("/<lang>/")
@app.route("/<lang>/<page>")
def page(lang, page="home"):

    #First check language exists in the database
    if not validate_language(lang):
        abort(404)
#        return "Language not implemented"
    #Check if page is in page list, otherwise throw error page for _that language_
    if page not in get_page_list(lang):
        abort(404)
#        return "Page not implemented"

    content=get_page_content(page,lang)
    content['lang']=lang

    return render_template("index.html", content=content)


@app.route("/profile")
@login_required
def profile():
    rstr="Profile for "+str(current_user.get_id())
    return rstr

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged out','success')
    return redirect('/')

@app.route("/manage-users",methods=["GET","POST"])
def manage_users():
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT username,email from credentials")
    userlist=cursor.fetchall()[0]
    conn.close()

    return render_template('manageusers.html',users=userlist)


@app.route("/mod-panel")
@login_required
def panel_page():
    content=get_page_vars('en')
    return render_template('panel.html',content=content)




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_credentials(username,password):
            id = username
            user = User(id)
            login_user(user)
            flash('Logged in successfully','success')
            return redirect(request.args.get('next') or "/")
        else:
            flash('Logged in successfully','danger')
    content=get_page_vars('en')
    return render_template('login.html',content=content)



# handle login failed
@app.errorhandler(401)
def unauthorised_page(e):
    flash("You must be logged in to access this page","warning")
#    print("Endpoint: "+request.endpoint)
#    print("URL: "+request.url)
#    print("Referrer: "+request.url)

    return redirect(url_for('login',next=request.url))

@app.errorhandler(404)
def not_found(e):
    content=get_page_vars('en')
    return render_template('404.html', content=content), 404


@app.route("/favicon.ico")
def fav():
    abort(404)










if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8005)
#    from flup.server.fcgi import WSGIServer
#    WSGIServer(app, bindAddress="/var/www/htdocs/aid_app/fcgi.sock",umask=0).run()
