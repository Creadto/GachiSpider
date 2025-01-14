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
    result = soup.select("#print_area div.writerProfile dt strong")
    pass

if __name__ == "__main__":
    main("https://www.bobaedream.co.kr/view?code=strange&No=6441402")