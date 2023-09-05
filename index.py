import openai
import os
openai.api_key = os.getenv("OPENAI_API_KEY")

import requests, json
from bs4 import BeautifulSoup

import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

from flask import Flask, render_template, request, make_response, jsonify
from datetime import datetime, timezone, timedelta
app = Flask(__name__)

@app.route("/")
def index():
    homepage = "<h1>楊子青Python網頁</h1>"
    homepage += "<a href=/mis>MIS</a><br>"
    homepage += "<a href=/today>顯示日期時間</a><br>"
    homepage += "<a href=/welcome?nick=tcyang>傳送使用者暱稱</a><br>"
    homepage += "<a href=/about>子青簡介網頁</a><br>"
    homepage += "<br><a href=/read>讀取Firestore資料</a><br>"
    homepage += "<br><a href=/movie>讀取開眼電影即將上映影片，寫入Firestore</a><br>"
    return homepage

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1>"

@app.route("/today")
def today():
    tz = timezone(timedelta(hours=+8))
    now = datetime.now(tz)
    return render_template("today.html", datetime = str(now))

@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    user = request.values.get("nick")
    return render_template("welcome.html", name=user)

@app.route("/about")
def about():
    return render_template("aboutme.html")

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/read")
def read():
    Result = ""     
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.order_by("mail", direction=firestore.Query.DESCENDING).get()    
    for doc in docs:         
        Result += "文件內容：{}".format(doc.to_dict()) + "<br>"    
    return Result

@app.route("/movie")
def movie():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".filmListAllX li")
    lastUpdate = sp.find("div", class_="smaller09").text[5:]

    for item in result:
        picture = item.find("img").get("src").replace(" ", "")
        title = item.find("div", class_="filmtitle").text
        movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
        show = item.find("div", class_="runtime").text.replace("上映日期：", "")
        show = show.replace("片長：", "")
        show = show.replace("分", "")
        showDate = show[0:10]
        showLength = show[13:]

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "lastUpdate": lastUpdate
         }

        doc_ref = db.collection("電影").document(movie_id)
        doc_ref.set(doc)
    return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate 

@app.route("/search")
def search():
    info = ""     
    collection_ref = db.collection("電影")
    #docs = collection_ref.where("title","==", "鬼修女II").get()
    docs = collection_ref.order_by("showDate").get()
    for doc in docs:
        if "：" in doc.to_dict()["title"]: 
            info += "片名：" + doc.to_dict()["title"] + "<br>" 
            info += "海報：" + doc.to_dict()["picture"] + "<br>"
            info += "影片介紹：" + doc.to_dict()["hyperlink"] + "<br>"
            info += "片長：" + doc.to_dict()["showLength"] + " 分鐘<br>" 
            info += "上映日期：" + doc.to_dict()["showDate"] + "<br><br>"           
    return info

@app.route("/searchQ", methods=["POST","GET"])
def searchQ():
    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]
        info = ""     
        collection_ref = db.collection("電影")
        #docs = collection_ref.where("title","==", "鬼修女II").get()
        docs = collection_ref.order_by("showDate").get()
        for doc in docs:
            if MovieTitle in doc.to_dict()["title"]: 
                info += "片名：" + doc.to_dict()["title"] + "<br>" 
                info += "影片介紹：" + doc.to_dict()["hyperlink"] + "<br>"
                info += "片長：" + doc.to_dict()["showLength"] + " 分鐘<br>" 
                info += "上映日期：" + doc.to_dict()["showDate"] + "<br><br>"           
        return info
    else:  
        return render_template("input.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action =  req.get("queryResult").get("action")
    #msg =  req.get("queryResult").get("queryText")
    #info = "動作：" + action + "； 查詢內容：" + msg
    if (action == "rateChoice"):
        rate =  req.get("queryResult").get("parameters").get("rate")
        if (rate == "輔12級"):
            rate = "輔導級(未滿十二歲之兒童不得觀賞)"
        elif (rate == "輔15級"):
            rate = "輔導級(未滿十五歲之人不得觀賞)"
        info = "您選擇的電影分級是：" + rate + "，相關電影：\n"

        collection_ref = db.collection("子青電影")
        docs = collection_ref.get()
        result = ""
        for doc in docs:
            dict = doc.to_dict()
            if rate in dict["rate"]:
                result += "片名：" + dict["title"] + "\n"
                result += "介紹：" + dict["hyperlink"] + "\n\n"
        info += result
    elif (action == "MovieDetail"): 
        cond =  req.get("queryResult").get("parameters").get("FilmQ")
        keyword =  req.get("queryResult").get("parameters").get("any")
        info = "您要查詢電影的" + cond + "，關鍵字是：" + keyword + "\n\n"
        if (cond == "片名"):
            collection_ref = db.collection("子青電影")
            docs = collection_ref.get()
            found = False
            for doc in docs:
                dict = doc.to_dict()
                if keyword in dict["title"]:
                    found = True 
                    info += "片名：" + dict["title"] + "\n"
                    info += "海報：" + dict["picture"] + "\n"
                    info += "影片介紹：" + dict["hyperlink"] + "\n"
                    info += "片長：" + dict["showLength"] + " 分鐘\n"
                    info += "分級：" + dict["rate"] + "\n" 
                    info += "上映日期：" + dict["showDate"] + "\n\n"
            if not found:
                info += "很抱歉，目前無符合這個關鍵字的相關電影喔"
    elif (action == "CityWeather"):
        city =  req.get("queryResult").get("parameters").get("city")
        token = "rdec-key-123-45678-011121314"
        url = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=" + token + "&format=JSON&locationName=" + str(city)
        Data = requests.get(url)
        Weather = json.loads(Data.text)["records"]["location"][0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        Rain = json.loads(Data.text)["records"]["location"][0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
        MinT = json.loads(Data.text)["records"]["location"][0]["weatherElement"][2]["time"][0]["parameter"]["parameterName"]
        MaxT = json.loads(Data.text)["records"]["location"][0]["weatherElement"][4]["time"][0]["parameter"]["parameterName"]
        info = city + "的天氣是" + Weather + "，降雨機率：" + Rain + "%"
        info += "，溫度：" + MinT + "-" + MaxT + "度"

    return make_response(jsonify({"fulfillmentText": info}))

@app.route("/chatgpt")
def chatgpt():
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="靜宜大學資管系楊子青老師在獲獎方面？",
        max_tokens=128,
        temperature=0.5,
    )
    msg = response.choices[0].text
    return msg

#if __name__ == "__main__":
    #app.run()