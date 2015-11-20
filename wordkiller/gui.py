# -*- coding: utf-8 -*-

import wx
from core import *

class ModifyDialog( wx.Dialog ):
    def __init__( self, parent, word, row ):
        wx.Dialog.__init__( self, parent, title = word.word  )

        self.word = word
        self.parent = parent
        self.row = row

        sizer = wx.FlexGridSizer( cols = 2, vgap = 5, hgap = 5 )

        # create control
        self.levelText = wx.TextCtrl( self, value = str(word.level) )
        self.rightText = wx.TextCtrl( self, value = str(word.right) )
        self.wrongText = wx.TextCtrl( self, value = str(word.wrong) )
        saveButton = wx.Button( self, label = 'Save' )
        deleteButton = wx.Button( self, label = 'Delete' )

        # add to sizer
        sizer.Add( wx.StaticText( self, label = 'level' ), 0,
                wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
        sizer.Add( self.levelText, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add( wx.StaticText( self, label = 'Right' ), 0,
                wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
        sizer.Add( self.rightText, 0, wx.EXPAND|wx.ALL, 5 )
        sizer.Add( wx.StaticText( self, label = 'Wrong' ), 0,
                wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
        sizer.Add( self.wrongText, 0, wx.EXPAND|wx.ALL, 5 )

        sizer.Add( saveButton, 0, wx.CENTER|wx.ALL, 5 )
        sizer.Add( deleteButton, 0, wx.CENTER|wx.ALL, 5 )

        # bind events
        self.Bind( wx.EVT_BUTTON, self.onSave, saveButton )
        self.Bind( wx.EVT_BUTTON, self.onDelete, deleteButton )

        # end
        self.SetSizer( sizer )
        sizer.Fit( self )

    def onSave( self, e ):
        '''
        ret = wx.MessageBox( 'Are you sure to save?', 'Comfirm',
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) 
        if ret == wx.NO:
            return
        '''
        self.word.level = int(self.levelText.GetValue())
        self.word.right = int(self.rightText.GetValue())
        self.word.wrong = int(self.wrongText.GetValue())

        self.Destroy()
        self.parent.showLine( self.row, self.word )

    def onDelete( self, e ):
        self.parent.vocabulary.deleteWord( self.word )
        self.parent.wordlist.DeleteItem( self.row )
        self.parent.refresh()

        self.Destroy()

class ListFrame( wx.Frame ):
    colName = ( 'Word', 'Level', 'Right', 'Wrong', 'delta', 'Last', 'Add', 'Next' )
    sortKey = ( lambda x:x.word, lambda x:x.level, lambda x:-x.right, lambda
            x:-x.wrong, lambda x:x.right-x.wrong, lambda x:-x.lastTime, lambda
            x:-x.addTime, lambda x:-x.nextTime )

    def __init__( self, parent, vocabulary ):
        wx.Frame.__init__( self, parent, title = "List", size = (800,600) )

        self.wordlist = wx.ListCtrl( self, style = wx.LC_REPORT )

        self.vocabulary = vocabulary

        # insert row and col
        for i in range( len(self.colName) ):
            self.wordlist.InsertColumn( i, self.colName[i] )
        for i in range( len(self.vocabulary.vocabulary) ):
            self.wordlist.InsertStringItem( i, '' )

        self.refresh()

        for i in range( len(self.colName) ):
            self.wordlist.SetColumnWidth( i, wx.LIST_AUTOSIZE )

        self.Bind( wx.EVT_LIST_COL_CLICK, self.onColClick, self.wordlist )
        self.Bind( wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivited, self.wordlist )

    def refresh( self, key = lambda x:-x.addTime ):
        # make a copy
        self.voc = self.vocabulary.vocabulary[0:]
        self.voc.sort( key = key )
        for i in range( len(self.voc) ):
            self.showLine( i, self.voc[i] )

    def showLine( self, row, word ):
        self.wordlist.SetStringItem( row, 0, word.word )
        self.wordlist.SetStringItem( row, 1, str(word.level) + ' ' )
        self.wordlist.SetStringItem( row, 2, str(word.right) )
        self.wordlist.SetStringItem( row, 3, str(word.wrong) )
        self.wordlist.SetStringItem( row, 4, str(word.right - word.wrong) )
        self.wordlist.SetStringItem( row, 5, easyTime(word.lastTime) )
        self.wordlist.SetStringItem( row, 6, easyTime(word.addTime) )
        self.wordlist.SetStringItem( row, 7, easyTime(self.vocabulary.
            nextReviewTime( word )) )

    def onColClick( self, e ):
        col = e.GetColumn()

        self.refresh( key = self.sortKey[col] )

    def onItemActivited( self, e ):
        dialog = ModifyDialog( self, self.vocabulary.maplist[e.GetText()],
                e.GetIndex() )
        dialog.Show()

class MainFrame( wx.Frame ):
    DATAFILE = 'book1.db'
    DICTFILE = 'dict15000.db'
    WORD_NUM = 20 # words per page
    STR = {}
    STR['no_word'] = ( 'No words need to be reviewd', 'No Words' )
    STR['submit_cf'] = ( 'Are you sure to submit?', 'Confirm' )
    STR['complete'] = ( 'All words have been reviewd', 'Well Done' )
    STR['quit_cf'] = ( 'Are you sure to quit?', 'Confirm' )
    STR['add_word'] = ( 'Type word list, a word a line', 'Add Word' )

    def __init__( self, parent, title ):
        wx.Frame.__init__( self, parent, title = title, size = ( 800, 700 ) )

        self.initVB()
        self.initUI()

        self.Centre()
        self.Show()
##
##          INITATION
##
    def initVB( self ):
        self.vocabulary = VocabularyBook( self.DATAFILE )
        self.config = self.vocabulary.config

        # word unicode to str
        for word in self.vocabulary.vocabulary:
            word.word = word.word.encode( 'utf-8' )

        self.vocabulary.updateQueue()
        self.state = 'home'

    def initUI( self ):
        panel = self.panel = wx.Panel( self )

        mainSizer = self.mainSizer = wx.BoxSizer( wx.VERTICAL )

        #--------------- Top Button Line ---------------#
        sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.reviewButton  = wx.Button( panel, label = u'复习' )
        self.addButton     = wx.Button( panel, label = u'添加' )
        self.listallButton = wx.Button( panel, label = u'查看' )
        self.helpButton    = wx.Button( panel, label = u'帮助' )
        self.settingButton = wx.Button( panel, label = u'设置' )
        self.firstButton = self.reviewButton

        sizer.Add( self.reviewButton,  0, wx.ALL, 5 )
        sizer.Add( self.addButton,     0, wx.ALL, 5 )
        sizer.Add( self.listallButton, 0, wx.ALL, 5 )
        sizer.Add( self.helpButton,    0, wx.ALL, 5 )
        sizer.Add( self.settingButton, 0, wx.ALL, 5 )

        mainSizer.Add( sizer, 0, wx.EXPAND, 5 )
        mainSizer.Add( wx.StaticLine(panel, -1), 0, wx.EXPAND )

        #------------------ Word View -------------------#
        self.wordSizer = wx.BoxSizer( wx.VERTICAL )
        indicate  = self.indicate  = []
        wordTexts = self.wordTexts = []
        detail    = self.detail    = []

        font = self.reviewButton.GetFont()

        # add word detail lines
        for i in range( self.WORD_NUM + 4 ):
            sizer = wx.BoxSizer( wx.HORIZONTAL )

            indicate.append( wx.StaticText( panel, label = '     ' ) )
            wordTexts.append( wx.StaticText( panel, size = (100, -1),
                style = wx.ALIGN_RIGHT ) )
            detail.append( wx.StaticText( panel, label = '' ) )

            sizer.Add( indicate[i],  0, wx.ALIGN_CENTER_VERTICAL )
            sizer.Add( wordTexts[i], 0, wx.ALIGN_CENTER_VERTICAL )
            sizer.Add( detail[i],    0, wx.EXPAND|wx.LEFT, 10 )
            # set font size
            font.SetPointSize( 11 )
            wordTexts[i].SetFont( font )
            font.SetPointSize(10)
            detail[i].SetFont( font )

            self.wordSizer.Add( sizer, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 2 )

        mainSizer.Add( self.wordSizer, 0, wx.EXPAND|wx.LEFT, self.WORD_NUM )
        mainSizer.Add( wx.StaticLine(panel, -1), 0, wx.EXPAND )

        #-------------- Bottom Button Line --------------#
        sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.submitButton  = wx.Button( panel, label = u'提交' )
        self.remainText = wx.StaticText( panel, label = u'还剩 %3d 个'
                % len(self.vocabulary.reviewQueue) )
        self.timeText  = wx.StaticText( panel, label = u'用时 5:30  '  )

        sizer.Add( self.submitButton, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
        sizer.Add( wx.StaticText(panel, label = '' ), 1, wx.EXPAND )
        sizer.Add( self.timeText,     0, wx.ALIGN_CENTER|wx.ALL, 5 )
        sizer.Add( self.remainText,   0, wx.ALIGN_CENTER|wx.ALL, 5 )

        mainSizer.Add( sizer, 1, wx.EXPAND)

        #------------------ Bind Event ------------------#
        # close
        self.Bind( wx.EVT_CLOSE, self.onCloseWindow )
        # review
        self.Bind( wx.EVT_BUTTON, self.startReview, self.reviewButton )
        # add
        self.Bind( wx.EVT_BUTTON, self.onAddWords, self.addButton )
        # list all
        self.Bind( wx.EVT_BUTTON, self.onListAll, self.listallButton )
        # help
        self.Bind( wx.EVT_BUTTON, self.onHelp, self.helpButton )

        #------------------- The End --------------------#
        panel.SetSizer( mainSizer )
        mainSizer.Fit( self )

##
##          REVIEW MODE                    
##
    def startReview( self, e ):
        self.state = 'review'

        length = self.vocabulary.updateQueue()
        self.remainText.SetLabel( u'还剩 ' + str(length) + u' 个' )

        # no words in review queue
        if length == 0:
            wx.MessageBox( self.STR['no_word'][0], self.STR['no_word'][1],
                    wx.OK )
            return

        self.nowlist = self.vocabulary.popMany( self.WORD_NUM )
        self.isForgotten = [False] * self.WORD_NUM
        self.forgetFirstTime = []

        #---------- show words ----------#
        self.showInit()
        self.now = -1

        #----------- mainloop -----------#
        self.Bind( wx.EVT_KEY_DOWN, self.onKeyDownReview )
        self.reviewButton.SetLabel( u'退出复习' )
        self.Bind( wx.EVT_BUTTON, self.stopReview, self.reviewButton )
        self.Bind( wx.EVT_BUTTON, self.onSubmit, self.submitButton )

        # setting for focus
        self.firstButton.Bind( wx.EVT_SET_FOCUS, self.onSetFocus_b )
        self.SetFocus()

    def stopReview( self, e ):
        #------------- unbind -----------#
        self.Unbind( wx.EVT_KEY_DOWN)
        self.reviewButton.SetLabel( u'复习' )
        self.Bind( wx.EVT_BUTTON, self.startReview, self.reviewButton )
        self.firstButton.Unbind( wx.EVT_SET_FOCUS )

        #---------- clean screen --------#
        self.cleanPage()
        self.state = 'home'

    def onSubmit( self, e ):
        ret = wx.MessageBox( self.STR['submit_cf'][0], self.STR['submit_cf'][1],
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) 

        if ret == wx.NO:
            return

        for i in range( len(self.nowlist) ):
            word = self.vocabulary.maplist[self.nowlist[i]]
            if self.isForgotten[i]:
                self.forgetFirstTime.append(word.word)
                word.doWrong()
                self.vocabulary.forcePush( word.word )
            else:
                word.doRight()

        #------------- redraw -----------#
        self.cleanPage()
        length = self.vocabulary.updateQueue()
        self.remainText.SetLabel( u'还剩 ' + str(length) + u' 个' )

        if length > 0:
            self.nowlist = self.vocabulary.popMany( self.WORD_NUM )
            self.isForgotten = [False] * self.WORD_NUM
            self.showInit()
            self.now = -1
            self.SetFocus()
        else:
            wx.MessageBox( self.STR['complete'][0], self.STR['complete'][1],
                    wx.OK )
            self.stopReview( None )

    def showInit( self ):
        for i in range( len(self.nowlist) ):
            word = self.vocabulary.maplist[self.nowlist[i]]
            if self.config['show']['word']:
                self.wordTexts[i].SetLabel( word.word )

    def cleanPage( self ):
        for i in range( len(self.nowlist) ):
            self.indicate[i].SetLabel( '' )
            self.wordTexts[i].SetLabel( '' )
            self.wordTexts[i].SetForegroundColour( 'black' )
            self.detail[i].SetLabel( '' )
        self.indicate[self.now].SetLabel( '' )

    def showWord( self ):
        word = self.vocabulary.maplist[self.nowlist[self.now]]

        self.detail[self.now].SetLabel( word.toString() )
        self.wordTexts[self.now].SetLabel( word.word )

    def pronounce( self, word, style = None ):
        if style != None:
            self.snd = playMP3( ''.join(('.\\audio\\', style, '\\' ,
                                            word , '.mp3')) )
        else:
            self.snd = playMP3( ''.join(('.\\audio\\',self.vocabulary.
                getConfig( 'phonetic' ), '\\' , word , '.mp3')) )

    def refresh( self, previous, now ):
        word = self.vocabulary.maplist[self.nowlist[now]]

        self.indicate[previous].SetLabel( '' )
        self.indicate[now].SetLabel( u'→' )
        self.detail[previous].SetLabel( '' )

        self.pronounce( word.word )

    def onKeyDownReview( self, e ):
        previous = self.now

        code = e.GetKeyCode()

        if code == ord('W'):
            self.now = (self.now - 1) % len( self.nowlist )
        elif code == ord('S'):
            self.now = (self.now + 1) % len( self.nowlist )
        elif code == ord('A'):
            self.showWord()
        elif code == ord('D'):
            word = self.vocabulary.maplist[self.nowlist[self.now]]
            if self.isForgotten[self.now]:
                self.isForgotten[self.now] = False
                self.wordTexts[self.now].SetForegroundColour( 'black' )
                self.wordTexts[self.now].SetLabel( word.word )
            else:
                self.isForgotten[self.now] = True
                self.wordTexts[self.now].SetForegroundColour( 'red' )
                self.wordTexts[self.now].SetLabel( '*' )
                #self.wordTexts[self.now].SetLabel( word.word )
        elif code == ord('Q'):
            self.pronounce( self.nowlist[self.now], 'uk' )
        elif code == ord('E'):
            self.pronounce( self.nowlist[self.now], 'us' )
        elif code == ord('F'):
            self.onSubmit( None )
            return
        elif code == ord('X'):
            self.wordTexts[self.now].SetLabel( '' )

        if previous != self.now:
            self.refresh( previous, self.now  )

    # for some focus problems
    def onSetFocus_b( self, e ):
        if e.GetWindow() == self:
            e.Skip()
        else:
            self.SetFocus()
##
##          ADD WORDS
##
    def onAddWords( self, e ):
        dialog = wx.TextEntryDialog( None, self.STR['add_word'][0],
            self.STR['add_word'][1], '\n'*10, wx.OK|wx.CANCEL|wx.TE_MULTILINE )
        dialog.SetValue( '' )

        if dialog.ShowModal() == wx.ID_OK:
            rawlist = dialog.GetValue().split( '\n' )
            wordlist = []

            # delete space line
            for line in rawlist:
                if line.strip():
                    wordlist.append( line )

            self.vocabulary.addMany( wordlist, self.DICTFILE )

        dialog.Destroy()

##
##          LIST ALL
##
    def onListAll( self, e ):
        frame = ListFrame( self, self.vocabulary )
        frame.Center()
        frame.Show()
##
##          HELP
##
    def onHelp( self, e ):
        h = wx.TipWindow( self.helpButton, "Todo" )

##
##          QUIT
##
    def onCloseWindow( self, e ):
        #ret = wx.MessageBox( self.STR['quit_cf'][0], self.STR['quit_cf'][1],
                #wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) 

        ret = wx.YES
        if ret == wx.YES:
            self.Destroy()
        else:
            e.Veto()


app = wx.App()
MainFrame( None, 'WorlKiller' )
app.MainLoop()
