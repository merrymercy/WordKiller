# -*- coding: utf-8 -*-
import sqlite3
import re
import time
import random
import os

class Word:
    def __init__( self, word, phonetic, meaning ):
        self.word = word
        self.phonetic = phonetic
        self.meaning = meaning
        self.right = 0
        self.wrong = 0
        self.record = ''
        self.level = 0
        self.addTime = time.time()
        self.lastTime = self.addTime
        self.nextTime = 0
        self.inWrong = False

    def doRight( self ):
        self.right += 1
        self.lastTime = time.time()
        if self.inWrong:
            self.doRecord( False )
        else:
            self.doRecord( True )

        self.inWrong = False

    def doWrong( self ):
        self.wrong += 1
        self.inWrong = True
        self.lastTime = time.time()

    # record and upgrade/degrade
    def doRecord( self, passFirstTime ):
        if passFirstTime:
            self.record += 'R'
        else:
            self.record += 'W'

        if self.record[-3:] == 'RRR':
            self.level += 3
        elif self.record[-2:] == 'RR':
            self.level += 2
        elif self.record[-3:] == 'WWW':
            self.level = 0
        elif self.record[-2:] == 'WW':
            self.level -= 1
        else:
            self.level += 1

        print self.record

    def sets( self, **params ):
        for item in params:
            setattr( self, item, params[item] )

    # return whether the word match the condition to review
    def match( self, interval ):
        if self.level < 0: level = 0
        else:              level = self.level

        now = time.time()
        if now - self.lastTime > interval[level]:
            return True
        else:
            return False

    def isSimilar( self, word ):
        if self.word == word:
            return False

        i = j = 0
        length = min( len(self.word), len(word) )

        while i < length and self.word[i] == word[i]:
            i += 1
        while j < length and self.word[-j-1] == word[-j-1]:
            j += 1

        return 1.0 * (i + j) / ((len(self.word)+len(word)) / 2) > 0.7

    def toString( self ):
        strlist = []
        strlist.append( self.meaning )
        strlist.append( ''.join((self.phonetic[0], '  ', self.phonetic[1])) )
        strlist.append( '   '.join(('level:', str(self.level),
            'right:', str(self.right), 'wrong:', str(self.wrong))) )
        strlist.append( '   '.join(('last:', easyTime(self.lastTime)+' ago')) )
        strlist.append( '   '.join(('add:', easyTime(self.addTime)+' ago')) )

        return '\n'.join( strlist )

    def printSelf( self ):
        print self.word, self.phonetic[0].encode('gbk','ignore'), self.\
                        phonetic[1].encode('gbk','ignore')
        print self.meaning
        print 'level:', self.level
        print 'right:', self.right, '   wrong', self.wrong
        print 'addTime:', time.asctime( time.localtime(self.addTime) )
        print 'lastTime:', time.asctime( time.localtime(self.lastTime) )
        print 'record:', self.record, self.inWrong

class VocabularyBook:
    def __init__( self, filename ):
        # store word objects
        self.vocabulary = []
        # words to review
        self.reviewQueue = []
        # map name to word objects
        self.maplist = {}

        self.filename = filename
        self.data = {}
        self.config = {}

        self.loadData()

    def __del__( self ):
        self.storeData()

##
##          LOAD & STORE
##
    def loadData( self ):

        # open database
        if os.path.exists( self.filename ):
            db = sqlite3.connect( self.filename )
        else:
            print self.filename, 'does not exist, create it'
            db = sqlite3.connect( self.filename )
            db.execute( ''' CREATE TABLE vocabulary (
                WORD            TEXT,
                PHONETIC_US     TEXT,
                PHONETIC_UK     TEXT,
                MEANING         TEXT,
                RIGHT           INT,
                WRONG           INT,
                RECORD          TEXT,
                LEVEL           INT,
                ADDTIME         REAL,
                LASTTIME        REAL,
                NEXTTIME        REAL,
                INWRONG         INT
                )
                ''' )
            db.execute( ''' CREATE TABLE reviewqueue ( WORD TEXT ) ''' )
            db.execute( ''' CREATE TABLE config ( KEY TEXT, VALUE TEXT ) ''' )
            db.commit()

        # load vocabulary from database
        cursor = db.execute( 'SELECT word, phonetic_us, phonetic_uk, meaning,'
                   'right, wrong, record, level, addtime, lasttime, nexttime,'
                   'inwrong FROM vocabulary' )
        for row in cursor:
            word = Word( row[0], (row[1],row[2]), row[3] )
            word.right   = row[4];  word.wrong = row[5]
            word.record  = row[6];  word.level = row[7]
            word.addTime = row[8];  word.lastTime = row[9]
            word.nextTime= row[10]; word.inWrong = True if row[11] else False

            self.vocabulary.append( word )

        # load review queue from database
        row = db.execute( 'SELECT word FROM reviewqueue' ).fetchone()
        if row and row[0] != '':
            self.reviewQueue = row[0].split(',')

        # load configration from datebase
        cursor = db.execute( 'SELECT key, value FROM config' )
        for row in cursor:
            self.config[row[0]] = self.config[row[1]]

        # init configration
        self.initConfig()

        # add every word to word list
        for item in self.vocabulary:
            self.maplist[item.word] = item

        self.db = db

    def storeData( self ):
        db = self.db

        for word in self.vocabulary:
            db.execute( 'UPDATE vocabulary SET'
                ' word=' + '"' + word.word + '"' +
                ',phonetic_us=' + '"' + word.phonetic[0] + '"' +
                ',phonetic_uk=' + '"' + word.phonetic[1] + '"' +
                ',meaning='  + '"' + word.meaning + '"' +
                ',right='    + str(word.right) +
                ',wrong='    + str(word.wrong) +
                ',record='   + '"' + word.record + '"' +
                ',level='    + str(word.level) +
                ',addtime='  + str(word.addTime) +
                ',lasttime=' + str(word.lastTime) +
                ',nexttime=' + str(word.nextTime) +
                ',inwrong='  + ('1' if word.inWrong else '0') +
                ' WHERE word="' + word.word + '"' )

        #if self.reviewQueue != []:
        string = ','.join( self.reviewQueue )
        db.execute( 'UPDATE reviewqueue SET word="' + string + '"' )

        db.commit()
        db.close()

##
##          CONFIG SETTINGS
##
    def initConfig( self ):
        # convert days and hours to seconds
        def day( day ):
            return day * 3600*24
        def hour( hour ):
            return hour * 3600

        cfg = self.config

        if 'interval' not in cfg:
            print 'add interval to config'
            '''
            cfg['interval'] = [ -1, 30, 30, 30, 30, day(1),
                            day(1), day(2), day(3), day(5), day(5), day(5),
                            day(10), day(15), day(20), day(30) ]
            '''
            cfg['interval'] = [ -1, hour(6), hour(12), day(1), day(1), day(1),
                            day(1), day(2), day(3), day(5), day(5), day(5),
                            day(10), day(15), day(20), day(30) ]+20*[day(30)]

        if 'show' not in cfg:
            print 'add show to config'
            cfg['show'] = {}
            cfg['phonetic'] = 'uk'
            cfg['show']['phonetic']= True
            cfg['show']['word']    = False
            cfg['show']['meaning'] = True

    def setConfig( self, key, value ):
        self.config[key] = value

    def getConfig( self, key ):
        return self.config[key]

##
##          REVIEW QUEEN
##
    def updateQueue( self ):
        for item in self.vocabulary:
            if (item.word not in self.reviewQueue) and item.match(self.config\
                    ['interval'] ):
                self.reviewQueue.append( item.word )
        return len( self.reviewQueue )

    def popMany( self, n ):
        if n > len(self.reviewQueue):
            n = len(self.reviewQueue) 
        ret = self.reviewQueue[0:n]
        del self.reviewQueue[0:n]
        random.shuffle( ret )
        return ret

    def forcePush( self, word ):
        if word in self.maplist:
            self.reviewQueue.append( word )
        else:
            print 'ERROR : add an unexisted word to queue'
##
##          WORD I/O
##
    def addWord( self, word, dictname ):
        if word in self.maplist:
            print 'ERROR:', word, 'existed already'
            return

        ret = Dictionary(dictname).getword(word)
        if ret:
            self.db.execute( 'INSERT INTO vocabulary VALUES (?' + ',?'*11 + ')',
                ( ret.word, ret.phonetic[0], ret.phonetic[1], ret.meaning,
                  ret.right, ret.wrong, ret.record, ret.level, ret.addTime,
                  ret.lastTime, ret.nextTime, 1 if ret.inWrong else 0 ) )
            self.db.commit()

            self.vocabulary.append( ret )
            self.maplist[word] = self.vocabulary[-1]
            print 'add', word

    def addMany( self, wordlist, dictname ):
        for word in wordlist:
            self.addWord( word, dictname )

    def deleteWord( self, word ):
        if word.word not in self.maplist:
            print 'ERROR:', 'delete unexisted word', word
            return

        self.db.execute( 'DELETE from vocabulary WHERE word="' +word.word+ '"' )
        self.db.commit()

        if word.word in self.reviewQueue:
            self.reviewQueue.remove( word.word )
        del self.maplist[word.word]
        self.vocabulary.remove( word )

    # ugly, for temporary use
    def nextReviewTime( self, word ):
        # a margical expression
        word.nextTime = time.time() - (self.config['interval'][word.level]
                    - (time.time() - word.lastTime) )
        return word.nextTime

##
##          PRINT FOR DEBUGGING
##
    def printQueue( self ):
        print '---------- Queue Begin ----------'
        for word in self.reviewQueue:
            self.maplist[word].printSelf()
        print '----------- Queue End -----------'


    def printData( self ):
        print '---------- Data Begin ----------'
        for word in self.vocabulary:
            word.printSelf()
            if self.vocabulary.index(word) % 10 == 0:
                raw_input( 'Enter' )
        print '----------- Data End -----------'

    def printConfig( self ):
        print '---------- Config Begin ----------'
        for item in self.config:
            print item, ':', self.config[item]
        print '----------- Config End -----------'

class Dictionary:
    def __init__( self, filename ):
        self.dictname = filename


    def getword( self, word ):

        # todo: move connection to __init__ and optimize vocabulary.addMany()
        if os.path.exists( self.dictname ):
            db = sqlite3.connect( self.dictname )
        else:
            print 'ERROR:', self.dictname, 'does not exist'
            return None

        row = db.execute( 'SELECT word, phonetic_us, phonetic_uk,'
                'meaning FROM dictionary WHERE word="' + word + '"').fetchone()

        if row:
            return Word( row[0], (row[1], row[2]), row[3] )
        else:
            print "ERROE: cann't find word", word, 'in', self.dictname
            return None

        db.close()

    def printList( self ):
        pass

# return a easily read time string
def easyTime( oldTime ):
    delta = time.time() - oldTime
    if delta < 0:
        return "0"
    elif delta < 3600:
        return "%d minutes" % (delta / 60)
    elif delta < 24 * 3600:
        return "%d hours" % (delta / 3600)
    else:
        return "%d days" % (delta / (24 * 3600))

 
# play pronounciation mp3 file
def playMP3( filename ):
    import pymedia.muxer as muxer
    import pymedia.audio.acodec as acodec
    import pymedia.audio.sound as sound

    f = open( filename, 'rb' ) 
    data= f.read( 10000 )
    dm = muxer.Demuxer( 'mp3' )
    frames = dm.parse( data )
    dec = acodec.Decoder( dm.streams[ 0 ] )
    frame = frames[0]
    r = dec.decode( frame[ 1 ] )
    snd = sound.Output( r.sample_rate, r.channels, sound.AFMT_S16_LE )
    if r: snd.play( r.data )

    while True:
        data = f.read(512)
        if len(data)>0:
            r = dec.decode( data )
            if r: snd.play( r.data )
        else:
            break
    return snd

if __name__ == '__main__' :

    '''
    wordlist = ( 'zinc','spite','luxury','setback','primarily','exquisite',
                 'decimal','considerable','barren','yoke','inlet','distort',
                 'slack','fabricate','yield','defiance','cholesterol','yield',
                 'reward','maintain','arrogant','afford','ignite','flat',
                 'define','harmony','paradise','plea','merely','ponder',)

    mybook = VocabularyBook( 'CORE.db' )
    mybook.loadData()

    mybook.addMany( wordlist[:10], 'dict.txt' )

    mybook.printData()
    
    mybook.storeData()
    '''

