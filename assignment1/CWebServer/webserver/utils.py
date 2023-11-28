from bs4 import BeautifulSoup
from markdown import markdown


def md_to_text(text: str):
    html = markdown(text)
    return BeautifulSoup(html, features="html.parser").get_text()
