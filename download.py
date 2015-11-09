# -*- coding:utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import time
import os


class dictDownloader():
    def __init__( self, listFile, dictFile ):
        self.todownlist = []
        self.errorlist = []
        self.wordlist = []
        self.count = 0
        
        self.listFile = listFile
        self.dictFile = dictFile

        self.s =requests.Session()
        self.baseURL = 'http://cn.bing.com/dict/search?q='

    def downWord( self, word ):
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
        r = self.s.get( re.search( "http:.*?mp3", tag_a['onclick'] ).group(),
                                                        stream = True)
        open(''.join(('.\\us\\',word,'.mp3')), 'wb').write(r.raw.read())

        # UK phonetic
        div = div.next_sibling.next_sibling
        phonetic.append( div.text )
        # UK MP3 file
        tag_a = div.next_sibling.a
        r = self.s.get( re.search( "http:.*?mp3", tag_a['onclick'] ).group() )

        open(''.join(('.\\uk\\',word,'.mp3')), 'wb').write(r.raw.read())

        return ''.join( ('<e>',word.encode('utf-8'),'</e>\n','<p>',
               '<us>', phonetic[0].encode('utf-8').strip(), '</us>',
               '<uk>', phonetic[1].encode('utf-8').strip(), '</uk>',
               '</p>\n', '<c>', meaning.encode('utf-8'), '</c>\n') )
  
    def setListFile( self, filename ):
        for line in open( filename, 'r' ):
            self.todownlist.append( line.strip() )

    def setList( self, todownlist ):
        self.todownlist = todownlist
 
    def downList( self ):
        for item in self.todownlist:
            try:
                word = self.downWord( item )
                self.wordlist.append( word )
            except Exception, e:
                self.errorlist.append( item )
                print 'Error in downloading', item
                print e

    def storeFile( self, filename = 'default.txt', mode = 'w' ):
        print '------ store to', filename, '------'

        count = 0
        f = open( filename, mode )
        for item in self.wordlist:
            count += 1
            print '------ store ', str(count),item[3:item.find('/')-1], '------'
            f.write( item )
        f.close()

    def getErrorList( self ):
        return self.errorlist

    def main( self ):
        print '=START TO DOWNLOAD='
        timer = time.clock()

        try:
            self.setListFile( self.listFile )
            self.downList()
        except Exception, e:
            print 'ERROR:', e
        finally:
            self.storeFile( self.dictFile )

        print '=DOWNLOAD FINISHED='
        print 'Time used:', time.clock() - timer

        if self.errorlist:
            print 'Error occurred in downloading these words:'
            for line in self.errorlist:
                print line
        raw_input( '<enter>' )

if __name__ == '__main__':
    dict = dictDownloader( 'list.txt', 'data.txt' )
    dict.main()
