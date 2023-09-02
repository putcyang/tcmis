import requests
from bs4 import BeautifulSoup
url = "http://www.atmovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"

sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select(".filmListAllX li")
info = ""

for item in result:
  picture = item.find("img").get("src").replace(" ", "")
  title = item.find("div", class_="filmtitle").text
  hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
  show = item.find("div", class_="runtime").text.replace("上映日期：", "")
  show = show.replace("片長：", "")
  show = show.replace("分", "")
  showDate = show[0:10]
  showLength = show[13:]
  info += picture + "\n" + title + "\n" + hyperlink + "\n" + showDate + "\n" + showLength + "\n\n"
print(info)

