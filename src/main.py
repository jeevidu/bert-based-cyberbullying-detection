
from flask_cors import CORS
from flask import *
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'your_secret_key'
import sqlite3 
import os
import datetime
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = BASE_DIR / "uploads"
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

UPLOAD_FOLDER.mkdir(exist_ok=True)
from src.prediction import *

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def connect():
    db_path = BASE_DIR / "database" / "chat.db"
    return sqlite3.connect(db_path)
def get_user_age_by_id(uid):
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            CAST((julianday('now') - julianday(dob)) / 365.25 AS INTEGER) AS age 
        FROM users
        WHERE uid = ?
    ''', (uid,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]  # age
    else:
        return None  # UID not found
def predict_text(text):
    try:
        from keras.preprocessing.text import one_hot
        from keras.utils import pad_sequences
        import re
        from nltk.stem.snowball import SnowballStemmer
        from nltk.corpus import stopwords
        from tensorflow.keras.models import load_model
        import numpy as np

        # Load the saved model
        model = load_model("one.h5")
        # Text cleaning
        text_cleaning = "\b0\S*|\b[^A-Za-z0-9]+"

        stop_words = stopwords.words('english')

        def preprocess_filter(text, stem=False):
            text = re.sub(text_cleaning, " ", str(text.lower()).strip())
            tokens = []
            for token in text.split():
                if token not in stop_words:
                    if stem:
                        stemmer = SnowballStemmer(language='english')
                        token = stemmer.stem(token)
                    tokens.append(token)
            return " ".join(tokens)

        def one_hot_encoded(text, vocab_size=5000, max_length=40):
            hot_encoded = one_hot(text, vocab_size)
            return hot_encoded

            # word embedding pipeline

        def word_embedding(text):
            preprocessed_text = preprocess_filter(text)
            return one_hot_encoded(preprocessed_text)

        # Define the function for prediction input processing

        import torch
        from transformers import BertTokenizer, BertForSequenceClassification

        # Load model and tokenizer
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)  # Adjust labels
        MODEL_PATH = BASE_DIR / "models" / "modelBert1.pth"
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        model.to(device)
        model.eval()

        # Example prediction
        text = "This is an example tweet."
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)

        with torch.no_grad():
                outputs = model(**inputs)
                prediction = torch.argmax(outputs.logits, dim=1).item()

        print("Prediction:", prediction)
    except:
        pass

import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# List of 50 cyberbullying-related emojis
cyberbullying_emojis = {
    "🤡", "🐍", "💀", "🤢", "🚮", "🖕", "🤬", "👎", "🙄", "😡",
    "😤", "😠", "😾", "😒", "😶‍🌫️", "🤮", "☠️", "🖤", "😓", "😭",
    "👿", "🫥", "🙃", "😈", "💔", "👺", "👹", "😑", "😵‍💫", "🧐",
    "😥", "😓", "🥀", "🙁", "🫤", "🖍", "🗑️", "😐", "😞", "🖕",
    "🙅", "🙆‍♂️", "🗣️", "🤨", "🥴", "😕", "😵", "🤯", "👊", "💣"
}

def contains_cyberbullying_emoji(text):
    """Check if the text contains any cyberbullying-related emojis."""
    found_emojis = [e["emoji"] for e in emoji.emoji_list(text)]  # Extract emojis
    detected = [e for e in found_emojis if e in cyberbullying_emojis]  # Check against list
    return detected

def analyze_sentiment(text):
    """Analyze the sentiment of the text."""
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)

def contains_emoji(text):
    return any(char in emoji.EMOJI_DATA for char in text)


@app.route('/', strict_slashes=False)
def home():
    return render_template("index.html") 
@app.route('/chat/updatechat', methods=["POST"], strict_slashes=False)
def updatechat():
    r=request.json
    mydb = connect()
    d="update chat set senderid ='%s',receiverid ='%s',message ='%s',currentdata ='%s',filename ='%s',status ='%s' where cid='%s'"%(r['senderid'],r['receiverid'],r['message'],r['currentdata'],r['filename'],r['status'],r['cid'])
    mycursor = mydb.cursor()
    mycursor.execute(d)
    mydb.commit()
    mydb.close()
    return 's'
    
@app.route('/chat/viewchat', methods=["POST"], strict_slashes=False)
def viewchat():
        mydb = connect()
        mycursor = mydb.cursor()
        tx="select *   from chat"
        mycursor.execute(tx)
        e=mycursor.fetchall()
        mydb.close()
        return json.dumps(e)


@app.route('/chat/deletechat', methods=["POST"], strict_slashes=False)
def deletechat():
        r=request.json
        mydb = connect()
        mycursor = mydb.cursor()
        tx="delete from chat where cid={0}".format(r['id'])
        mycursor.execute(tx)
        mydb.commit()
        mydb.close()
        return 's'
@app.route('/insertusers', methods=["POST","GET"], strict_slashes=False)
def insertusers():
    if request.method=="POST":
        r=dict(request.form)
        r['designation']=""
        r['isapproved']="yes"
        mydb = connect()
        mycursor = mydb.cursor()
        tx = 'select uid from users order by uid desc limit 1'
        mycursor.execute(tx)
        e = mycursor.fetchall()
        if len(e) == 0:
                eid = 1
        else:
                eid = e[0][0]+1
        d="insert into users(uid,uname,email,mobile,Designation,password,isapproved,dob)values ('%s','%s','%s','%s','%s','%s','%s','%s')"%(eid,r['uname'],r['email'],r['mobile'],r['designation'],r['password'],r['isapproved'],r["dob"])
        mycursor = mydb.cursor()
        mycursor.execute(d)
        mydb.commit()
        mydb.close()
        return redirect("/login")
    else:
          return render_template("reg.html")
    
@app.route('/chat/updateusers', methods=["POST"], strict_slashes=False)
def updateusers():
    r=request.json
    mydb = connect()
    d="update users set uname ='%s',email ='%s',mobile ='%s',role ='%s',password ='%s',isapproved ='%s' where uid='%s'"%(r['uname'],r['email'],r['mobile'],r['role'],r['password'],r['isapproved'],r['uid'])
    mycursor = mydb.cursor()
    mycursor.execute(d)
    mydb.commit()
    mydb.close()
    return 's'
@app.route('/chat/approveusers', methods=["POST"], strict_slashes=False)
def approveusers():
    r=request.json
    mydb = connect()
    d="update users set isapproved ='%s' where uid='%s'"%("yes",r['uid'])
    mycursor = mydb.cursor()
    mycursor.execute(d)
    mydb.commit()
    mydb.close()
    return 's'
    
@app.route('/chat/viewusers', methods=["POST"], strict_slashes=False)
def viewusers():
        mydb = connect()
        mycursor = mydb.cursor()
        tx="select *   from users"
        mycursor.execute(tx)
        e=mycursor.fetchall()
        mydb.close()
        return json.dumps(e)

@app.route('/chat/viewusersbyid', methods=["POST"], strict_slashes=False)
def viewusersbyid():
        r=request.json
        mydb = connect()
        mycursor = mydb.cursor()
        tx="select *   from users where uid!='%s'"%(r["id"])
        mycursor.execute(tx)
        e=mycursor.fetchall()
        mydb.close()
        return json.dumps(e)
@app.route('/chat/deleteusers', methods=["POST"], strict_slashes=False)
def deleteusers():
        r=request.json
        mydb = connect()
        mycursor = mydb.cursor()
        tx="delete from users where uid={0}".format(r['id'])
        mycursor.execute(tx)
        mydb.commit()
        mydb.close()
        return 's'

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
# def emoji(text):
#     import emoji
#     import re
#     # Lowercase the text
#     text = text.lower()
#     # Demojify text
#     text = emoji.demojize(text)
#     # Remove URLs
#     text = re.sub(r'http\S+', '', text)
#     # Remove special characters
#     text = re.sub(r'[^a-zA-Z0-9\s:]', '', text)
#     return text
def textfromimage(input_image_path):
    import platform

    if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

    processed_image_path = BASE_DIR / "uploads" / "temp2.png"
    # Open the image
    im = Image.open(input_image_path)

    # Preprocess the image
    # Apply a median filter to reduce noise
    im = im.filter(ImageFilter.MedianFilter())

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(im)
    im = enhancer.enhance(2)  # Adjust the factor as needed

    # Convert to binary (black and white)
    im = im.convert('1')

    # Save the processed image for review
    im.save(processed_image_path)

    # Perform OCR on the processed image
    text = pytesseract.image_to_string(im, config='--psm 6')  # psm 6 assumes a single block of text

    return text
from nltk.sentiment import SentimentIntensityAnalyzer

from nltk.sentiment import SentimentIntensityAnalyzer

# Initialize VADER
sia = SentimentIntensityAnalyzer()

def get_sentiment_label(text):
    scores = sia.polarity_scores(text)
    compound = scores['compound']

    # Define thresholds
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"

@app.route("/insertchat", methods=["POST"], strict_slashes=False)
def insertchat():
    now = datetime.now()
    r = dict(request.form)
    r["senderid"] = session["id"]
    mydb = connect()
    mycursor = mydb.cursor()

    # Generate chat ID
    tx = "SELECT cid FROM chat ORDER BY cid DESC LIMIT 1"
    mycursor.execute(tx)
    e = mycursor.fetchall()
    eid = 1 if len(e) == 0 else e[0][0] + 1
    age=get_user_age_by_id(session["id"])
    

    textcyber=False
    emojicyber=False
    piccyber=False
    # Check if file is uploaded
    filename = ""
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != "":
            file_path = BASE_DIR / "static" / file.filename
            file.save(file_path)
            text=textfromimage("../static/"+file.filename)
            filename=file.filename
            try:
                text="".join(text.split("\n"))
                text=text.strip()
                print(text)
                out=prediction(text)
                print(out)
                if out!="not_cyberbullying":
                     piccyber=True
                     type=out
            except:
                 pass

    t=contains_emoji(r["message"])
    if t:
        # Detect cyberbullying emojis
        detected_emojis = contains_cyberbullying_emoji(r["message"])

        if detected_emojis:
            sentiment = analyze_sentiment(r["message"])
            print(f"⚠️ Cyberbullying emojis detected: {detected_emojis}")
            print(f"Sentiment analysis: {sentiment}")
            emojicyber=True
            type=''
            if sentiment["compound"] < -0.5:
                print("🚨 High likelihood of cyberbullying!")
                
        else:
            print("✅ No cyberbullying emojis detected.")
    out=prediction(r["message"])
    if out!="not_cyberbullying":
        textcyber=True
        type=out
        print(type)
    print(textcyber,emojicyber,piccyber)
    
    
    
    #Check for bullying words (Assuming `single_comment` handles this)
    if textcyber or emojicyber or piccyber:
        vader_score =get_sentiment_label(r["message"])
       
        if(vader_score!="Positive") and type!="gender" and type!="age":
            
            block_query = """
                SELECT counts FROM chatblock WHERE 
                (touser='%s' AND fromuser='%s') OR (touser='%s' AND fromuser='%s')
            """%(r["senderid"], r["receiverid"], r["receiverid"], r["senderid"])
            mycursor.execute(block_query)
            rx = mycursor.fetchone()
            print("working")
            c = 1 if rx is None else rx[0] + 1
            print(rx)
            if rx is None:
                block_insert = "INSERT INTO chatblock (fromuser, touser, ondate, counts) VALUES ('%s', '%s', '%s', '%s')"% (r["senderid"], r["receiverid"], now, c)
                mycursor.execute(block_insert)
            else:
                block_update = "UPDATE chatblock SET counts='%s', ondate='%s' WHERE fromuser='%s' AND touser='%s'"%(c, now, r["senderid"], r["receiverid"])
                mycursor.execute(block_update )

            mydb.commit()
            mydb.close()
            if textcyber:
                t="Message Cyberbully"
            elif emojicyber:
                t="Emoji Cyberbully"
            else:
                t="Image Cyberbully"
            return {"type":type,"data":t}
        else:
            # Insert message into database
            check="May contains bully"
    chat_insert = """
        INSERT INTO chat (cid, senderid, receiverid, message, currentdata, filename, status) 
        VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')
    """%(eid, r["senderid"], r["receiverid"], r["message"], now, filename, r["status"])
    mycursor.execute(chat_insert)
    mydb.commit()
    mydb.close()

    return "Message Sent"
@app.route('/getchat', methods=["POST"], strict_slashes=False)
def getchat():
        r=request.form
        mydb = connect()
        mycursor = mydb.cursor()
        tx="select *   from chat  desc where (senderid='%s' or receiverid='%s') and (senderid='%s' or receiverid='%s') order by currentdata"%(r["toid"],r["toid"],session["id"],session["id"])
        mycursor.execute(tx)
        e=mycursor.fetchall()
        mydb = connect()
        mycursor = mydb.cursor()
        tx="select *   from chatblock where (fromuser='%s' or touser='%s') and (fromuser='%s' or touser='%s')"%(r["toid"],r["toid"],session["id"],session["id"])
        mycursor.execute(tx)
        ex=mycursor.fetchone()
        data={"chat":e,"block":ex}
        mydb.close()
        print(data)
        return json.dumps(data)
@app.route('/chatscreen', methods=["get"])
def chatscreen():
    mydb = connect()
    mycursor = mydb.cursor()
    tx="select *   from users where uid!='%s'"%(session["id"])
    mycursor.execute(tx)
    e=mycursor.fetchall()
    mydb.close()
    return render_template("chatscreen.html",e=e)


@app.route('/login', methods=["post","get"])
def login():
    if request.method=="POST":
        r = dict(request.form)
        con = connect()
        x="select uid,uname,isapproved from users where email='%s' and password='%s'"%(r["email"], r["password"])
        v = con.execute(x).fetchone()
        if v!=None:  
            session["id"]=v[0]
            session["name"]=v[1]
            return redirect("/chatscreen")
        else:
              return render_template("login.html",error="Unable to Login")
    return render_template("login.html")
from datetime import datetime
@app.route('/viewfeed')
def feed():
    conn = connect()
    cur = conn.cursor()

    # Get all feeds with user info
    cur.execute('''
        SELECT feeds.fid, feeds.feeds, feeds.image, feeds.transdate, users.uname
        FROM feeds
        JOIN users ON feeds.uid = users.uid
        ORDER BY feeds.fid DESC
    ''')
    feed_list = cur.fetchall()

    # Get all comments grouped by fid
    cur.execute('''
        SELECT feeddetails.fid, feeddetails.commenttext, users.uname 
        FROM feeddetails
        JOIN users ON feeddetails.uid = users.uid
    ''')
    comments = cur.fetchall()

    # Group comments by feed id
    comment_dict = {}
    for fid, text, uname in comments:
        comment_dict.setdefault(fid, []).append({'text': text, 'uname': uname})

    conn.close()
    return render_template('feed.html', feeds=feed_list, comments=comment_dict)


@app.route('/add_feed', methods=['POST'])
def add_feed():
    feeds = request.form['feeds']
    image = ""
    uid = request.form['uid']  # Normally from session
    
    # Connect to the database
    conn = connect()
    cur = conn.cursor()

    # Retrieve the last inserted id from the feeds table
    cur.execute("SELECT MAX(fid) FROM feeds")
    last_id = cur.fetchone()[0]

    # If there's no last_id, set it to 1 (first entry in the table)
    if last_id is None:
        new_id = 1
    else:
        new_id = last_id + 1  # Increment the last_id by 1

    # Insert the new feed with the incremented id
    cur.execute("INSERT INTO feeds (fid, feeds, image, transdate, uid) VALUES (?, ?, ?, ?, ?)",
                (new_id, feeds, image, datetime.now().date(), uid))
    conn.commit()
    conn.close()

    return redirect(url_for('feed'))

from flask import flash, redirect, url_for

@app.route('/add_comment/<int:fid>', methods=['POST'])
def add_comment(fid):
    
    comment = request.form['comment']
    uid = session["id"] # Normally from session
    textcyber = False
    emojicyber = False
    piccyber = False
    type = ""

    # Check if comment contains emojis
    t = contains_emoji(comment)
    if t:
        # Detect cyberbullying emojis
        detected_emojis = contains_cyberbullying_emoji(comment)

        if detected_emojis:
            sentiment = analyze_sentiment(comment)
            print(f"⚠️ Cyberbullying emojis detected: {detected_emojis}")
            print(f"Sentiment analysis: {sentiment}")
            emojicyber = True
            type = ''
            if sentiment["compound"] < -0.5:
                print("🚨 High likelihood of cyberbullying!")
        else:
            print("✅ No cyberbullying emojis detected.")

    # Check if comment text is cyberbullying using some model or logic
    out = prediction(comment)
    if out != "not_cyberbullying":
        textcyber = True
        type = out
        print(type)

    print(textcyber, emojicyber, piccyber)

    # Check if there is any form of cyberbullying (text, emoji, or pic)
    if textcyber or emojicyber or piccyber:
        vader_score = get_sentiment_label(comment)
        if vader_score != "Positive":
            # Flash a message for cyberbullying
            if textcyber:
                t = "Message Cyberbully"
            elif emojicyber:
                t = "Emoji Cyberbully"
            flash(f"Warning: {t} detected. Comment not posted.")
            return redirect(url_for('feed'))  # Redirect back to the feed page

    # If no cyberbullying detected, insert the comment into the database
    conn = connect()
    cur = conn.cursor()

    # Get the last id and increment for the new comment
    cur.execute("SELECT MAX(fdid) FROM feeddetails")
    last_id = cur.fetchone()[0]
    if last_id is None:  # Handle the case where no entries exist
        last_id = 0
    new_id = last_id + 1  # Increment the last ID for the new comment

    # Insert comment details into the database
    cur.execute("INSERT INTO feeddetails (fdid, commenttext, fid, uid) VALUES (?, ?, ?, ?)", 
                (new_id, comment, fid, uid))
    conn.commit()
    conn.close()

    return redirect(url_for('feed'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)