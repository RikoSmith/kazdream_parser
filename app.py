"""
Zakon.kz News Parser by Riko

How to use it:
    
    1. Run this app (as a development server)
    2. Go to 'localhost:5000' in browser

    P.S.: downloads will take time (as it will make #number_of_published_news requests ) since 
    no persistance (database) have been implemeted to reduece number of unnecessary requests
   
"""



from flask import Flask, render_template, send_from_directory
from bs4 import BeautifulSoup
import requests 
import json
import datetime
import csv

app = Flask(__name__, static_url_path='')

# setting up a headers to avoid blocking from web site and immitate real user. Headers are copied from typical request
# sent by my browser and machine (linux)
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
    "Accept-Encoding": "gzip, deflate, br", 
    "Accept-Language": "ru,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,ru-RU;q=0.6", 
    "Upgrade-Insecure-Requests": "1", 
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36"
}

# this function is for getting a list of all news and its urls
def news_all():
    
    
    # this part turned out to be not needing the scrapper as inspecting (and a little bit debugging) the web site
    # one can find and api call (inner HTML javascript) to this endpoint - http://static.zakon.kz/zakon_cache/category/2/2020/06-11_news.json
    # which is essentially the qucik list of all the news in all languages in JSON. In essense, it can be considered as open API
    # as it does not need any API keys or authorization. It will save us computation time. The JSON already contains title, date, short description,
    # url to image and comments count

    # getting today's date to inject in url
    now = datetime.datetime.now()
    day = month = None
    
    # adding 0s before dates 
    if now.day < 10:
        day = '0' + str(now.day)
    else:
        day = str(now.day)

    if now.month < 10:
        month = '0' + str(now.month)
    else:
        month = str(now.month)



    url = 'http://static.zakon.kz/zakon_cache/category/2/' + str(now.year) + '/' + month + '-' + day + '_news.json'
    print(url)
    # getting JSON from akon news site
    response = requests.get(url, headers=headers)

    # check if we get anything, if not return error message (for now)
    if response.status_code != 200:
        return ("Error! Status Code: " + str(response.status_code))
    
    # returning the result as a dict
    return json.loads(response.content)



# ROUTES --------------------------------------------------------------
# main page just for views and graphical interface
@app.route('/')
def main_page():

    news_dict = news_all()
    
    return render_template("index.html", news = news_dict)


# this route is responsible for scraping each news page
@app.route('/news')
def update_json():


    # call '/news' route to update global news list (NEWS) 
    news_dict = news_all()

    # inference through each news item. This time there is not easy API call (i could not find), so we have to 
    # request each and every news url in the list and add additional data to NEWS document
    for news in news_dict["items"]:
        response = requests.get(news["url"], headers=headers)

        # check for error code (if we have problems here then zakon.kz's data is corrupted)
        if response.status_code != 200:
            return ("Error! One of the news links are invalid! Status Code: " + str(response.status_code) + " \nURL: " + news["url"])

        # parsing with bs4
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # parsing full text
        n_text = ""
        text = soup.find('div',attrs={'id':'initial_news_story'})
        
        # some news are formatted differently (probably older versions of site)
        if text is None:
            text = soup.find('div',attrs={'class':'WordSection1'})
            if text is None:
                continue
        
        n_text = text.getText()

        # adding new field (full text)
        news["full_text"] = n_text

    print(news_dict["items"])

    with open('static/news.csv', 'w',) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Title', 'Date', 'URL', 'Image URL', 'Language', 'Short Text', 'Full Text', 'Comments Count'])
        for news in news_dict["items"]:
            writer.writerow([news["id"], news["title"], news["date_print"], news["url"], news["img"], news["lang"], news["shortstory"], news["full_text"], news["comm_num"]])

    return app.send_static_file('news.csv')
