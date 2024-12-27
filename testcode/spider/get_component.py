""" 
    Title: What is the BeautifulSoup library?
    Description: Basic sample code for using the BeautifulSoup library.
"""
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as bs


def main(url):
    req = Request(url, headers={'User-Agent': "googling bot"})
    context = urlopen(req)
    soup = bs(context.read(), 'html.parser')
    result = soup.select("h3.post_subject")

if __name__ == "__main__":
    main("{your target url}")