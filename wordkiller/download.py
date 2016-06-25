# -*- coding:utf-8 -*-

import sqlite3
import re
import time
import os
import random

import requests
from bs4 import BeautifulSoup
from core import *

ips = (
    "42.51.4.25:80",
    "58.18.50.10:3128",
    "58.67.159.50:80",
    "60.191.153.12:3128",
    "60.191.157.155:3128",
    "60.191.158.211:3128",
    "60.191.166.130:3128",
    "60.191.167.11:3128",
    "60.191.167.93:3128",
    "60.191.170.52:3128",
    "60.191.170.122:3128",
)

header = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) '
                'Gecko/20100101 Firefox/41.0'
}



class dictDownloader():
    def __init__(self, dictFile):
        self.todownlist = []
        self.errorlist = []
        self.wordlist = []
        self.dictFile = dictFile
        self.count = 0

        # if do not exist, create the table
        if os.path.exists( self.dictFile ):
            db = sqlite3.connect( self.dictFile )
        else:
            print self.dictFile, 'does not exist, create it'
            db = sqlite3.connect( self.dictFile )
            db.execute( ''' CREATE TABLE dictionary (
                WORD            TEXT,
                PHONETIC_US     TEXT,
                PHONETIC_UK     TEXT,
                MEANING         TEXT,
                SENTENCE        TEXT
                )
                ''' )
        self.db = db
      
        self.s =requests.Session()
        self.s.headers = header

        self.baseURL = {
            'Bing'  : 'http://cn.bing.com/dict/search?q=',
            'ICIBA' : 'http://www.iciba.com/'
        }

    def randomProxy(self):
        # no use
        '''
        self.s.proxies = {
            "http" : "http://" + ips[random.randint(0, len(ips) - 1)]
        }
        '''

    def downWordICIBA(self, word):
        self.count += 1
        cur = self.db.execute(''.join(('SELECT word FROM dictionary WHERE '
                                        'word="', word, '"')) )
        if cur.fetchone():
            print word, 'already existed'
            return None

        print '------ download', str(self.count), word, '------'
        data = self.s.get(''.join((self.baseURL['ICIBA'], word)), timeout = 2)
        data.encoding = 'utf-8'
        soup = BeautifulSoup( data.text, 'html.parser' )

        # download meaning
        meaning = ''
        baseList =  soup.find( 'ul', class_ = 'base-list' )
        for item in baseList.find_all( 'li' ):
            # tmp = item.span.text.strip() + item.p.text.strip() + '\n'
            tmp = ''.join( (item.span.text.strip(),item.p.text.strip(),'\n'))
            tmp = tmp.replace(' ', '')
            tmp = tmp.replace(';', '; ')
            meaning = ''.join( (meaning, tmp) )

        # delete last newline
        meaning = meaning[:-1]

        # download pronunciation of UK and US
        phonetic = []

        # UK phonetic
        span = soup.find( 'div', class_ = "base-speak" ).span
        phonetic.append( span.text )
        # UK MP3 file
        span = span.next_sibling
        r = self.s.get( re.search( "http:.*?\.mp3", span['onmouseover']
                                ).group(), timeout = 2, stream = True )
        open(''.join(('.\\audio\\uk\\',word,'.mp3')),
                                    'wb').write(r.raw.read())

        # US phonetic
        span = span.next_sibling.next_sibling
        phonetic.append( span.text )
        # US MP3 file
        span = span.next_sibling
        r = self.s.get( re.search( "http:.*?\.mp3", span['onmouseover']
                                ).group(), timeout = 2, stream = True )
        open(''.join(('.\\audio\\us\\',word,'.mp3')),
                                    'wb').write(r.raw.read())
            

        # download sentence
        div = soup.find('div', class_ = 'article-tab')
        div = div.find_all( 'div', class_ = 'section-p' )[0].div
        sentence =  div.text.strip()

        return (word, phonetic[1].strip(), phonetic[0].strip(), meaning,
                                            sentence)

    def downWordBing(self, word):
        self.count += 1
        cur = self.db.execute(''.join(('SELECT word FROM dictionary WHERE '
                                        'word="', word, '"')) )
        if cur.fetchone():
            print word, 'already existed'
            return None
 
        print '------ download', str(self.count), word, '------'
        data = self.s.get( ''.join( (self.baseURL['Bing'], word) ) )
        data.encoding = 'utf-8'
        soup = BeautifulSoup( data.text, 'html.parser' )

        # download meaning
        meaning = ''
        for item in soup.find_all( 'span', class_ = "def" ):
            tmp = ''.join( (item.previous_sibling.text, ' ', item.text ) )
            meaning = ''.join( (meaning, tmp, '\n') )

        # delete 网络解释 and newline
        meaning = meaning[:meaning.find(u'网络')-1]

        # download pronunciation of UK and US
        phonetic = []
        # US phonetic
        div = soup.find( 'div', class_="hd_prUS" )
        phonetic.append( div.text )
        # US MP3 file
        tag_a = div.next_sibling.a
        r = self.s.get( re.search( "https:.*?mp3", tag_a['onclick'] ).group(),
                                                        stream = True )
        open(''.join(('.\\audio\\us\\',word,'.mp3')), 'wb').write(r.raw.read())

        # UK phonetic
        div = div.next_sibling.next_sibling
        phonetic.append( div.text )
        # UK MP3 file
        tag_a = div.next_sibling.a
        r = self.s.get( re.search( "https:.*?mp3", tag_a['onclick'] ).group(),
                                                        stream = True )

        open(''.join(('.\\audio\\uk\\',word,'.mp3')), 'wb').write(r.raw.read())

        # sentence
        sentence = ''
        div = soup.find_all('div', class_ = 'se_li1')[0].div
        sentence = div.text
        div = div.next_sibling
        sentence = ''.join((sentence, '\n', div.text))

        return (word, phonetic[0].strip(), phonetic[1].strip(),
                                            meaning, sentence)

        return (word.encode('utf-8'), phonetic[0].encode('utf-8').strip(),
                phonetic[1].encode('utf-8').strip(), meaning.encode('utf-8'))

    def updateWord(self, word):
        self.count += 1
        print '------ update', str(self.count), word, '------'
        data = self.s.get( ''.join( (self.baseURL['Bing'], word) ) )
        data.encoding = 'utf-8'
        soup = BeautifulSoup( data.text, 'html.parser' )

        # add sentence
        sentence = ''
        div = soup.find_all('div', class_ = 'se_li1')[0].div
        sentence = div.text
        div = div.next_sibling
        sentence = ''.join((sentence, '\n', div.text))

        self.db.execute('UPDATE dictionary SET'
            ' sentence='  + '"' + sentence.replace('"', '""') + '"' +
            ' WHERE word="' + word + '"')
        self.db.commit()

    # update the whole dictionary
    def updateList(self, words):
        recordfile = 'cpos.txt'
        # start from
        try:
            start = eval(open(recordfile, 'r').read()) + 1
        except Exception, e:
            start = 0
        self.count = start = max(0, start - 5)

        for i in range(start, len(words)):
            try:
                self.updateWord(words[i])
                open(recordfile, 'w').write(str(i))
            except Exception, e:
                self.errorlist.append( words[i] )
                print 'Error in updating', words[i]
                print e

    def setListFile( self, filename ):
        for line in open( filename, 'r' ):
            line = line.strip()
            if line != '':
                self.todownlist.append( line )

    def downList( self ):
        recordfile = 'apos.txt'
        # start from
        try:
            start = eval(open(recordfile, 'r').read()) + 1
        except Exception, e:
            start = 0
        self.count = start = max(0, start - 5)

        for i in range(start, len(self.todownlist)):
            try:
                word = self.downWordICIBA(self.todownlist[i])
                if word:
                    self.wordlist.append(word)
                if i % 20 == 19:
                    self.storeFile()
                    self.reportError('error.txt')
                    open(recordfile, 'w').write(str(i))
            except Exception, e:
                print 'Error in downloading', self.todownlist[i]
                print e
                if str(e).find('text') != -1:  # ignore words without phonetic
                    print 'ignored'
                else:
                    self.errorlist.append( self.todownlist[i] )

    def storeFile( self ):
        print '------ store to', self.dictFile, '------'

        # add words into database
        for item in self.wordlist:
            print '------ store ', item[0], '------'
            cur = self.db.execute(''.join(('SELECT word FROM dictionary '
                'WHERE word=', '"', item[0], '"')) )
            if cur.fetchone() == None:
                self.db.execute('INSERT INTO dictionary VALUES (?,?,?,?,?)',
                                                                    item)
            else:
                print 'already existed'

        self.db.commit()
        self.wordlist = []

    def getErrorList(self):
        return self.errorlist

    def reportError(self, errFile):
        if self.errorlist:
            err = open( errFile, 'a' )
            print 'Error occurred in updating these words:'
            for line in self.errorlist:
                print line
                err.write( line + '\n' )
            err.close()
        self.errorlist = []

    def __del__(self):
        self.db.close()

def updateDict(dictFile):
    print '=START TO DOWNLOAD='
    timer = time.clock()
    downloader = dictDownloader( dictFile )
    words = Dictionary(dictFile).getlist()

    try:
        downloader.updateList(words)
    except Exception, e:
        print 'ERROR:', e
    finally:
        downloader.storeFile()

    print '=DOWNLOAD FINISHED='
    print 'Time used:', time.clock() - timer

    #downloader.reportError(errFile)
    raw_input( '<enter>' )


# download a list file
def downFile( listFile, dictFile, errFile ):
    print '=START TO DOWNLOAD='
    timer = time.clock()
    downloader = dictDownloader( dictFile )
    downloader.setListFile( listFile )

    try:
        downloader.downList()
    except Exception, e:
        print 'ERROR:', e
    finally:
        downloader.storeFile()

    print '=DOWNLOAD FINISHED='
    print 'Time used:', time.clock() - timer

    downloader.reportError(errFile)
    raw_input( '<enter>' )

listFile = 'list.txt'
dictFile = 'dict15000.db'
errFile  = 'error.txt'

if __name__ == '__main__':
    updateDict(dictFile)
    #downFile( listFile, dictFile, errFile )
