# -*- coding: utf-8 -*-
import shelve
import re
import time
import random

class Word:
    def __init__( self, word, phonetic, meaning, right = 0, wrong = 0,
                        level = 0, lastTime = 0, force = False ):
        self.word = word
        self.phonetic = phonetic
        self.meaning = meaning
        self.right = right
        self.wrong = wrong
        self.record = []
        self.level = level
        self.addTime = time.time()
        self.lastTime = self.addTime
        self.nextTime = 0
        self.force = force

    def doRight( self ):
        self.right += 1
        self.lastTime = time.time()

    def doWrong( self ):
        self.wrong += 1
        self.lastTime = time.time()

    def doRecord( self, passFirstTime ):
        self.record.append( passFirstTime )

        self.level += 1

        if self.level >= 2:
            if False not in self.record[-2:]:
                self.level += 1
            if True not in self.record[-2:]:
                self.level -= 2

        print self.word, self.record


    def sets( self, **params ):
        for item in params:
            setattr( self, item, params[item] )

    def match( self, interval ):
        if self.level < 0: level = 0
        else:              level = self.level

        now = time.time()
        if now - self.lastTime > interval[level]:
            return True
        else:
            return False

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
        print 'record:', self.record

'''
a = Word( 'abc', ('/asd/','/fzc/'), 'meaning' )
a.printSelf()
a.doWrong()
print a.match( [-1, 0, 0] )
'''

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
        self.data = shelve.open( self.filename )

        # set config update here
        #del self.data['config']

        # load data from file
        if 'vocabulary' in self.data:
            self.vocabulary = self.data['vocabulary']
        if 'reviewQueue' in self.data:
            self.reviewQueue = self.data['reviewQueue']
        if 'config' in self.data:
            self.config = self.data['config']

        self.initConfig()

        # add every word to word list
        for item in self.vocabulary:
            self.maplist[item.word] = item

    def storeData( self ):
        self.data['vocabulary'] = self.vocabulary
        self.data['reviewQueue'] = self.reviewQueue
        self.data['config'] = self.config

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
                            day(10), day(15), day(20), day(30) ]

        if 'show' not in cfg:
            print 'add show to config'
            cfg['show'] = {}
            cfg['phonetic'] = 'uk'
            cfg['show']['phonetic']= True
            cfg['show']['word']    = True
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
            print 'ERROR : add an unexsited word to queue'
##
##          WORD I/O
##
    def addWord( self, word, dictname ):
        if word in self.maplist: # existed already
            print 'ERROR:', word, 'existed already'
            return

        ret = Dictionary(dictname).getword(word)
        if ret:
            self.vocabulary.append( ret )
            self.maplist[word] = self.vocabulary[-1]
            print 'add', word
        else:
            print "ERROE: cann't find word", word, 'in', dictname

    def addMany( self, wordlist, dictname ):
        for word in wordlist:
            self.addWord( word, dictname )

    def deleteWord( self, word ):
        self.reviewQueue.remove( word.word )
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
        self.text = open( filename ).read().decode( 'utf-8' )

    def getword( self, word ):
        pat = re.compile( ''.join(("<e>", word, "</e>.*?<p><us>(.*?)</us>",
                        "<uk>(.*?)</uk></p>.*?<c>(.*?)</c>" )), re.S )

        match = pat.search( self.text )
        if match:
            return Word( word, (match.group(1),match.group(2)), match.group(3))
        else:
            return None

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

    wordlist = ( 'zinc','spite','luxury','setback','primarily','exquisite',
                 'decimal','considerable','barren','yoke','inlet','distort',
                 'slack','fabricate','yield','defiance','cholesterol','yield',
                 'reward','maintain','arrogant','afford','ignite','flat',
                 'define','harmony','paradise','plea','merely','ponder',)

    mybook = VocabularyBook( 'book1.dat' )
    mybook.loadData()

    #mybook.addMany( wordlist, 'dict.txt' )

    #mybook.printData()
    
    mybook.storeData()

