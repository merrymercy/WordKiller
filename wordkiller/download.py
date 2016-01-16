# -*- coding:utf-8 -*-

import sqlite3
import re
import time
import os

import requests
from bs4 import BeautifulSoup

class dictDownloader():
    def __init__( self, dictFile ):
        self.todownlist = []
        self.errorlist = []
        self.wordlist = []
        self.dictFile = dictFile
        self.count = 0
       
        self.s =requests.Session()
        self.baseURL = 'http://cn.bing.com/dict/search?q='

    def downWord( self, word ):
        if os.path.exists( self.dictFile ):
            db = sqlite3.connect( self.dictFile )
            cur = db.execute(''.join(('SELECT word FROM dictionary WHERE word=',
                                    '"', word, '"')) )
            if cur.fetchone():
                print word, 'already existed'
                return None

 
        self.count += 1
        print '------ download', str(self.count), word, '------'
        data = self.s.get( ''.join( (self.baseURL, word) ) )
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

        return (word, phonetic[0].strip(), phonetic[1].strip(), meaning)

        return (word.encode('utf-8'), phonetic[0].encode('utf-8').strip(),
                phonetic[1].encode('utf-8').strip(), meaning.encode('utf-8'))

    def setListFile( self, filename ):
        for line in open( filename, 'r' ):
            line = line.strip()
            if line != '':
                self.todownlist.append( line )

    def setList( self, todownlist ):
        self.todownlist = todownlist
 
    def downList( self ):
        for item in self.todownlist:
            try:
                word = self.downWord( item )
                if word:
                    self.wordlist.append( word )
            except Exception, e:
                self.errorlist.append( item )
                print 'Error in downloading', item
                print e

    def storeFile( self ):
        print '------ store to', self.dictFile, '------'

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
                MEANING         TEXT
                )
                ''' )

        count = 0
        # add words into database
        for item in self.wordlist:
            count += 1
            print '------ store ', item[0], '------'

            cur = db.execute(''.join(('SELECT word FROM dictionary WHERE word=',
                                    '"', item[0], '"')) )
            if cur.fetchone() == None:
                db.execute( 'INSERT INTO dictionary VALUES (?,?,?,?)', item )
            else:
                print 'already existed'

        db.commit()
        db.close()

    def getErrorList( self ):
        return self.errorlist

listFile = 'list.txt'
dictFile = 'dict15000.db'
errFile  = 'error.txt'

if __name__ == '__main__':

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

        errorlist = downloader.getErrorList()
        if errorlist:
            err = open( errFile, 'a' )
            print 'Error occurred in downloading these words:'
            for line in errorlist:
                print line
                err.write( line + '\n' )
            err.close()
        raw_input( '<enter>' )

    downFile( listFile, dictFile, errFile )
