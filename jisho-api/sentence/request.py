from pydantic import BaseModel, ValidationError
from pathlib import Path
import json
import re
import pprint
import urllib
import requests
from typing import List
from bs4 import BeautifulSoup

from jisho import console
from jisho.util import CLITagger
from rich.markdown import Markdown
from .cfg import SentenceConfig

class RequestMeta(BaseModel):
    status: int

class SentenceRequest(BaseModel):
    meta: RequestMeta
    data: List[SentenceConfig]

    def __len__(self):
        return len(self.data)

    def rich_print(self):
        for d in self.data:
            console.print(f"[white][[red]jp[white]]")
            console.print(CLITagger.bullet(d.japanese))
            console.print(f"[white][[blue]en[white]]")
            console.print(CLITagger.bullet(d.en_translation))
            console.print(Markdown('---'))


class Sentence:
    URL = 'https://jisho.org/search/'
    ROOT = Path.home() / '.jisho/data/sentence/'

    @staticmethod
    def sentences(soup):
        res = soup.find_all('div', {"class": "sentence_content"})

        sts = []
        for r in res:
            s1_jp = r.find_all('li')
            s1_en = r.find_all('span', {"class": "english"})[0].text

            b = ""
            for s in s1_jp:  
                u = s.find('span', {"class": "unlinked"}).text
                b += u
                try:
                    f = s.find('span', {"class": "furigana"}).text
                    b += f"({f})"
                except:
                    pass
            sts.append({
                "japanese": b,
                "en_translation": s1_en
            })

        return sts

    @staticmethod
    def request(word, cache=False):
        url = Sentence.URL + urllib.parse.quote(word+" #sentences")
        toggle = False

        if cache and (Sentence.ROOT / (word+'.json')).exists():
            toggle = True
            with open(Sentence.ROOT / (word+'.json'), 'r') as fp:
                r = json.load(fp)
        else:
            r = requests.get(url).content
        soup = BeautifulSoup(r, 'html.parser')

        r = SentenceRequest(
            **{
                "meta": {
                    "status": 200,
                },
                "data": Sentence.sentences(soup)
            }
        )
        if not len(r):
            console.print(f"[red bold][Error] [white] No matches found for {word}.")
            return None
        if cache and not toggle:
            Sentence.save(word, r)
        return r

    @staticmethod
    def save(word, r):
        Sentence.ROOT.mkdir(exist_ok=True)
        with open(Sentence.ROOT / f"{word}.json", 'w') as fp:
            json.dump(r.dict(), fp, indent=4, ensure_ascii=False)