# -*- coding: utf-8 -*-

import wx
import winsound
from core import *

class ModifyDialog(wx.Dialog):
    def __init__(self, parent, word, row):
        wx.Dialog.__init__(self, parent, title = word.word)

        self.word = word
        self.parent = parent
        self.row = row

        sizer = wx.FlexGridSizer(cols = 2, vgap = 5, hgap = 5)

        # create control
        self.levelText = wx.TextCtrl(self, value = str(word.level))
        self.rightText = wx.TextCtrl(self, value = str(word.right))
        self.wrongText = wx.TextCtrl(self, value = str(word.wrong))
        saveButton = wx.Button(self, label = 'Save')
        deleteButton = wx.Button(self, label = 'Delete')

        # add to sizer
        sizer.Add(wx.StaticText(self, label = 'level'), 0,
                wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(self.levelText, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label = 'Right'), 0,
                wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(self.rightText, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label = 'Wrong'), 0,
                wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(self.wrongText, 0, wx.EXPAND|wx.ALL, 5)

        sizer.Add(saveButton, 0, wx.CENTER|wx.ALL, 5)
        sizer.Add(deleteButton, 0, wx.CENTER|wx.ALL, 5)

        # bind events
        self.Bind(wx.EVT_BUTTON, self.onSave, saveButton)
        self.Bind(wx.EVT_BUTTON, self.onDelete, deleteButton)

        # end
        self.SetSizer(sizer)
        sizer.Fit(self)

    def onSave(self, e):
        ret = wx.MessageBox('Are you sure to save?', 'Comfirm',
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) 
        if ret == wx.NO:
            return

        self.word.level = int(self.levelText.GetValue())
        self.word.right = int(self.rightText.GetValue())
        self.word.wrong = int(self.wrongText.GetValue())

        self.Destroy()
        self.parent.showLine(self.row, self.word)

    def onDelete(self, e):
        ret = wx.MessageBox('Are you sure to delete?', 'Comfirm',
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) 
        if ret == wx.NO:
            return

        self.parent.vocabulary.deleteWord(self.word)
        self.parent.wordlist.DeleteItem(self.row)
        self.parent.refresh()

        self.Destroy()

class ListFrame(wx.Frame):
    colName = ('Word', 'Level', 'Right', 'Wrong', 'delta', 'Last', 'Add', 'Next')
    sortKey = (lambda x:x.word, lambda x:x.level, lambda x:-x.right, lambda
            x:-x.wrong, lambda x:x.right-x.wrong, lambda x:-x.lastTime, lambda
            x:-x.addTime, lambda x:-x.nextTime)

    def __init__(self, parent, vocabulary):
        wx.Frame.__init__(self, parent, title = "List", size = (800,600))

        self.wordlist = wx.ListCtrl(self, style = wx.LC_REPORT)

        self.vocabulary = vocabulary

        # insert row and col
        for i in range(len(self.colName)):
            self.wordlist.InsertColumn(i, self.colName[i])
        for i in range(len(self.vocabulary.vocabulary)):
            self.wordlist.InsertStringItem(i, '')

        self.refresh()

        for i in range(len(self.colName)):
            self.wordlist.SetColumnWidth(i, wx.LIST_AUTOSIZE)

        self.Bind(wx.EVT_LIST_COL_CLICK, self.onColClick, self.wordlist)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivited, self.wordlist)

    def refresh(self, key = lambda x:-x.addTime):
        # make a copy
        self.voc = self.vocabulary.vocabulary[0:]
        self.voc.sort(key = key)
        for i in range(len(self.voc)):
            self.showLine(i, self.voc[i])

    def showLine(self, row, word):
        self.wordlist.SetStringItem(row, 0, word.word)
        self.wordlist.SetStringItem(row, 1, str(word.level) + ' ')
        self.wordlist.SetStringItem(row, 2, str(word.right))
        self.wordlist.SetStringItem(row, 3, str(word.wrong))
        self.wordlist.SetStringItem(row, 4, str(word.right - word.wrong))
        self.wordlist.SetStringItem(row, 5, easyTime(word.lastTime))
        self.wordlist.SetStringItem(row, 6, easyTime(word.addTime))
        self.wordlist.SetStringItem(row, 7, easyTime(self.vocabulary.
            nextReviewTime(word)))

    def onColClick(self, e):
        col = e.GetColumn()

        self.refresh(key = self.sortKey[col])

    def onItemActivited(self, e):
        dialog = ModifyDialog(self, self.vocabulary.maplist[e.GetText()],
                e.GetIndex())
        dialog.Show()

class MainFrame(wx.Frame):
    DATAFILE = 'book1.db'
    DICTFILE = 'dict15000.db'
    WORD_NUM = 20 # words per page
    STR = {}
    STR['no_word'] = ('No words need to be reviewd', 'No Words')
    STR['submit_cf'] = ('Are you sure to submit?', 'Confirm')
    STR['complete'] = ('All words have been reviewd', 'Well Done')
    STR['quit_cf'] = ('Are you sure to quit?', 'Confirm')
    STR['add_word'] = ('Type word list, a word a line', 'Add Word')

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title = title, style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)

        self.initVB()
        self.initUI()

##
##          INITATION
##
    def initVB(self):
        self.vocabulary = VocabularyBook(self.DATAFILE)
        self.config = self.vocabulary.config

        # word unicode to str
        for word in self.vocabulary.vocabulary:
            word.word = word.word.encode('utf-8')

        self.vocabulary.updateQueue()
        self.state = 'home'

    def initUI(self):
        panel = self.panel = wx.Panel(self)

        mainSizer = self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        #--------------- Top Button Line ---------------#
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.reviewButton  = wx.Button(panel, label = u'复习')
        self.addButton     = wx.Button(panel, label = u'添加')
        self.listallButton = wx.Button(panel, label = u'查看')
        self.helpButton    = wx.Button(panel, label = u'帮助')
        self.settingButton = wx.Button(panel, label = u'设置')
        self.firstButton = self.reviewButton

        sizer.Add(self.reviewButton,  0, wx.ALL, 5)
        sizer.Add(self.addButton,     0, wx.ALL, 5)
        sizer.Add(self.listallButton, 0, wx.ALL, 5)
        sizer.Add(self.helpButton,    0, wx.ALL, 5)
        sizer.Add(self.settingButton, 0, wx.ALL, 5)

        mainSizer.Add(sizer, 0, wx.EXPAND, 5)
        mainSizer.Add(wx.StaticLine(panel, -1), 0, wx.EXPAND)

        #------------------ Word View -------------------#
        self.wordSizer = wx.BoxSizer(wx.VERTICAL)
        indicate  = self.indicate  = []
        wordTexts = self.wordTexts = []
        detail    = self.detail    = []

        font = self.reviewButton.GetFont()

        # add word detail lines
        for i in range(self.WORD_NUM + 4):
            sizer = wx.BoxSizer(wx.HORIZONTAL)

            indicate.append(wx.StaticText(panel, label = '     '))
            wordTexts.append(wx.StaticText(panel, size = (100, -1),
                style = wx.ALIGN_RIGHT))
            detail.append(wx.StaticText(panel, label = ''))

            sizer.Add(indicate[i],  0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(wordTexts[i], 0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(detail[i],    0, wx.EXPAND|wx.LEFT, 10)
            # set font size
            font.SetPointSize(11)
            wordTexts[i].SetFont(font)
            font.SetPointSize(10)
            detail[i].SetFont(font)

            self.wordSizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 2)

        mainSizer.Add(self.wordSizer, 0, wx.EXPAND|wx.LEFT, self.WORD_NUM)
        mainSizer.Add(wx.StaticLine(panel, -1), 0, wx.EXPAND)

        #-------------- Bottom Button Line --------------#
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.submitButton  = wx.Button(panel, label = u'提交')
        self.remainText = wx.StaticText(panel, label = u'还剩 %3d 个'
                % len(self.vocabulary.reviewQueue))
        self.timeText  = wx.StaticText(panel, label = ' ' * 20)

        sizer.Add(self.submitButton, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(wx.StaticText(panel, label = ''), 1, wx.EXPAND)
        sizer.Add(self.timeText,     0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(self.remainText,   0, wx.ALIGN_CENTER|wx.ALL, 5)

        mainSizer.Add(sizer, 1, wx.EXPAND)

        #------------------ Bind Event ------------------#
        # close
        self.Bind(wx.EVT_CLOSE, self.onCloseWindow)
        # review
        self.Bind(wx.EVT_BUTTON, self.startReview, self.reviewButton)
        # add
        self.Bind(wx.EVT_BUTTON, self.onAddWords, self.addButton)
        # list all
        self.Bind(wx.EVT_BUTTON, self.onListAll, self.listallButton)
        # help
        self.Bind(wx.EVT_BUTTON, self.onHelp, self.helpButton)
        # help
        self.Bind(wx.EVT_BUTTON, self.onSetting, self.settingButton)
        # handle all key events
        self.Bind(wx.EVT_CHAR_HOOK, self.onKeyDown)

        #------------------- The End --------------------#
        panel.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def onKeyDown(self, e):
        if self.state == 'review':
            self.onKeyDownReview(e)
        else:
            e.Skip()
##
##          REVIEW MODE                    
##
    def startReview(self, e):
        self.state = 'review'

        length = self.vocabulary.updateQueue()
        self.remainText.SetLabel(u'还剩 ' + str(length) + u' 个')

        # no words in review queue
        if length == 0:
            wx.MessageBox(self.STR['no_word'][0], self.STR['no_word'][1],
                    wx.OK)
            return

        self.nowlist = self.vocabulary.popMany(self.WORD_NUM)
        self.isForgotten = [False] * self.WORD_NUM
        self.forgetFirstTime = []

        #---------- show words ----------#
        self.showInit()
        self.now = 0
        self.refresh(-1, self.now)

        #----------- mainloop -----------#
        #self.Bind(wx.EVT_KEY_DOWN, self.onKeyDownReview)
        self.reviewButton.SetLabel(u'退出复习')
        self.Bind(wx.EVT_BUTTON, self.stopReview, self.reviewButton)
        self.Bind(wx.EVT_BUTTON, self.onSubmit, self.submitButton)

        #------------- timer ------------#
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(1000)
        self.seconds = 0

        self.SetFocus()

    def stopReview(self, e):
        #------------- unbind -----------#
        self.Unbind(wx.EVT_KEY_DOWN)
        self.Unbind(wx.EVT_TIMER)
        self.timer.Stop()
        self.firstButton.Unbind(wx.EVT_SET_FOCUS)

        self.reviewButton.SetLabel(u'复习')
        self.Bind(wx.EVT_BUTTON, self.startReview, self.reviewButton)

        #---------- clean screen --------#
        self.cleanPage()
        self.state = 'home'

    def onSubmit(self, e):
        ret = wx.MessageBox(self.STR['submit_cf'][0], self.STR['submit_cf'][1],
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) 

        if ret == wx.NO:
            return

        for i in range(len(self.nowlist)):
            word = self.vocabulary.maplist[self.nowlist[i]]
            if self.isForgotten[i]:
                self.forgetFirstTime.append(word.word)
                word.doWrong()
                self.vocabulary.forcePush(word.word)
            else:
                word.doRight()

        #------------- redraw -----------#
        self.cleanPage()
        length = self.vocabulary.updateQueue()
        self.remainText.SetLabel(u'还剩 ' + str(length) + u' 个')

        if length > 0:
            self.nowlist = self.vocabulary.popMany(self.WORD_NUM)
            self.isForgotten = [False] * self.WORD_NUM
            self.showInit()
            self.now = 0
            self.refresh(-1, self.now)
        else:
            wx.MessageBox(self.STR['complete'][0], self.STR['complete'][1],
                    wx.OK)
            self.stopReview(None)

    def showInit(self):
        for i in range(len(self.nowlist)):
            word = self.vocabulary.maplist[self.nowlist[i]]
            if self.config['show']['word']:
                self.wordTexts[i].SetLabel(word.word)

    def cleanPage(self):
        for i in range(len(self.nowlist)):
            self.indicate[i].SetLabel('')
            self.wordTexts[i].SetLabel('')
            self.wordTexts[i].SetForegroundColour('black')
            self.detail[i].SetLabel('')
        self.indicate[self.now].SetLabel('')

    def showWord(self):
        word = self.vocabulary.maplist[self.nowlist[self.now]]

        self.detail[self.now].SetLabel(word.toString())
        self.wordTexts[self.now].SetLabel(word.word)

    def pronounce(self, word, style = None):
        if style != None:
            self.snd = playMP3(''.join(('.\\audio\\', style, '\\' ,
                                            word , '.mp3')))
        else:
            self.snd = playMP3(''.join(('.\\audio\\',self.vocabulary.
                getConfig('phonetic'), '\\' , word , '.mp3')))

    def refresh(self, previous, now):
        word = self.vocabulary.maplist[self.nowlist[now]]

        self.indicate[previous].SetLabel('')
        self.indicate[now].SetLabel(u'→')
        self.detail[previous].SetLabel('')

        self.pronounce(word.word)

    def onKeyDownReview(self, e):
        previous = self.now

        code = e.GetKeyCode()
        if code == wx.WXK_UP or code == ord('['):
            self.now = (self.now - 1) % len(self.nowlist)
        elif code == wx.WXK_DOWN or code == ord(']'):
            self.now = (self.now + 1) % len(self.nowlist)
        elif code == wx.WXK_LEFT or code == wx.WXK_TAB:  # switch show detail
            if self.detail[self.now].GetLabel() == '':
                self.showWord()
            else:
                self.detail[self.now].SetLabel('')
                self.wordTexts[self.now].SetLabel('')
        elif code == wx.WXK_RIGHT or code == ord('\\'):  # mark forgetten
            word = self.vocabulary.maplist[self.nowlist[self.now]]
            if self.isForgotten[self.now]:
                self.isForgotten[self.now] = False
                self.wordTexts[self.now].SetForegroundColour('black')
                self.wordTexts[self.now].SetLabel(word.word)
            else:
                self.isForgotten[self.now] = True
                self.wordTexts[self.now].SetForegroundColour('red')
                self.wordTexts[self.now].SetLabel(self.wordTexts[self.now].
                                                            GetLabel())
        elif code == wx.WXK_NUMPAD1 or code == ord('1'): # pronounce
            self.pronounce(self.nowlist[self.now], 'uk')
        elif code == wx.WXK_NUMPAD2 or code == ord('2'): # pronounce
            self.pronounce(self.nowlist[self.now], 'us')
        elif code == wx.WXK_NUMPAD3 or code == ord('3'): # finish one page
            self.onSubmit(None)
            return
        elif code == wx.WXK_NUMPAD0 or code == ord('0'): # similar words
            word = self.vocabulary.maplist[self.nowlist[self.now]]
            string = ''
            for item in self.vocabulary.maplist:
                if word.isSimilar(item):
                    string += item + '\n'
            self.detail[self.now].SetLabel(string[:-1])
        elif code < 256 and chr(code).isalpha():         # spell
            spelling = self.wordTexts[self.now].GetLabel()
            spelling += chr(code).lower()
            self.wordTexts[self.now].SetLabel(spelling)
        elif code == wx.WXK_SPACE:                       # check spelling
            now = self.wordTexts[self.now].GetLabel()
            word = self.vocabulary.maplist[self.nowlist[self.now]]

            if now.lower() == word.word.lower():
                if self.detail[self.now].GetLabel() != '':
                    self.now = (self.now + 1) % len(self.nowlist)
                else:
                    self.wordTexts[self.now].SetLabel(word.word)
                    self.showWord()
            else:
                if self.detail[self.now].GetLabel() == '*':
                    self.now = (self.now + 1) % len(self.nowlist)
                else:
                    winsound.MessageBeep(winsound.MB_OK)
                    self.isForgotten[self.now] = True
                    self.wordTexts[self.now].SetForegroundColour('red')
                    self.wordTexts[self.now].SetLabel('')
        elif code == wx.WXK_BACK:                       # delete
            spelling = self.wordTexts[self.now].GetLabel()
            spelling = spelling[:-1]
            self.wordTexts[self.now].SetLabel(spelling)
 
        if previous != self.now:
            self.refresh(previous, self.now )

    def onTimer(self, e):
        self.seconds += 1
        self.timeText.SetLabel(u'用时 ' + '%d:%02d  ' %
                        (self.seconds / 60, self.seconds % 60) ) 

##
##          ADD WORDS
##
    def onAddWords(self, e):
        class AddWordDialog(wx.Dialog):
            bookList = ("CET4", "CET6", "TOELF")
            def __init__(self, vocabulary):
                wx.Dialog.__init__(self, None, title = "Add Words")
                self.vocabulary = vocabulary

                # create controls
                okButton = wx.Button(self, wx.ID_OK, label = "OK")
                cancelButton = wx.Button(self, wx.ID_CANCEL, label = "Cancel")
                multiText = self.multiText = wx.TextCtrl(self, value = "\n"*10,
                        style = wx.TE_MULTILINE)
                addButton = wx.Button(self, -1, label = "Quick Add")
                listChoice = self.listChoice = wx.Choice(self, -1,
                                            choices=AddWordDialog.bookList)
                numText = self.numText = wx.TextCtrl(self, value = "20",
                                                        size=(50,25))

                # top label and text entry
                mainSizer = wx.BoxSizer(wx.VERTICAL)
                mainSizer.Add(wx.StaticText(self, label = "Type word list, "
                        "one word a line"), 0, wx.TOP|wx.LEFT, 10)
                mainSizer.Add(multiText, 1, wx.ALL|wx.EXPAND, 10)

                # quick add button
                quickSizer = wx.BoxSizer(wx.HORIZONTAL)
                quickSizer.Add(wx.StaticText(self, label = "From "), 0,
                        wx.ALIGN_CENTER)
                quickSizer.Add(listChoice, 0, wx.ALIGN_CENTER)
                quickSizer.Add(wx.StaticText(self, label = " Randomly "), 0,
                        wx.ALIGN_CENTER)
                quickSizer.Add(addButton, 0, wx.ALIGN_CENTER)
                quickSizer.Add(numText, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, 5)
                quickSizer.Add(wx.StaticText(self, label = " Words"), 0,
                        wx.ALIGN_CENTER)
                mainSizer.Add(quickSizer, 0, wx.ALL, 10)

                # bottom buttons
                mainSizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)
                buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
                buttonSizer.Add(wx.StaticText(self, label = " "), 1, wx.EXPAND)
                buttonSizer.Add(okButton, 0, wx.RIGHT, 10)
                buttonSizer.Add(cancelButton, 0)
                mainSizer.Add(buttonSizer, 0, wx.ALL|wx.EXPAND, 5)

                self.SetSizer(mainSizer)
                self.Fit()

                # ctrl init
                multiText.SetFocus()
                multiText.SetValue('')
                listChoice.SetSelection(1)

                # bind event
                self.Bind(wx.EVT_BUTTON, self.onQuickAdd, addButton)
            def GetValue(self):
                return self.multiText.GetValue()

            def onQuickAdd(self, e):
                book = AddWordDialog.bookList[self.listChoice.GetSelection()]
                number = int(self.numText.GetValue())

                newWords = ''
                f = open("list\\" + book + ".txt")
                ct = 0
                wordList = f.readlines()
                random.shuffle(wordList)
                for word in wordList:
                    if ct >= number:
                        break

                    word = word.strip()
                    if word != '' and (word not in self.vocabulary):
                        newWords += word + '\n'
                        ct += 1

                self.multiText.SetValue(self.multiText.GetValue() + newWords)

                f.close()

        dialog = AddWordDialog(self.vocabulary.maplist)

        if dialog.ShowModal() == wx.ID_OK:
            rawlist = dialog.GetValue().split('\n')
            wordlist = []

            # delete space line
            for line in rawlist:
                if line.strip():
                    wordlist.append(line)

            self.vocabulary.addMany(wordlist, self.DICTFILE)

        dialog.Destroy()

##
##          LIST ALL
##
    def onListAll(self, e):
        frame = ListFrame(self, self.vocabulary)
        frame.Center()
        frame.Show()
##
##          HELP
##
    def onHelp(self, e):
        wx.MessageBox("1       play American pronounciation\n"
                      "2       play British  pronounciation\n"
                      "3       submit one page\n"
                      "0       show similar words\n"
                      "[        cursor up\n"
                      "]        cursor down\n"
                      "\        switch forget mark\n"
                      "Tab       switch detail view\n"
                      "Spave   check spelling\n"
                      , "Key Help");

    def onSetting(self, e):
        h = wx.TipWindow(self.settingButton, "Todo")

##
##          QUIT
##
    def onCloseWindow(self, e):
        #ret = wx.MessageBox(self.STR['quit_cf'][0], self.STR['quit_cf'][1],
                #wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) 

        if self.state == 'review':
            self.stopReview(None)

        ret = wx.YES
        if ret == wx.YES:
            self.Destroy()
        else:
            e.Veto()

class app(wx.App):
    def OnInit(self):
        frame = MainFrame(None, 'Word Killer')
        self.SetTopWindow(frame)
        frame.Centre()
        frame.Show()
        return 1

if __name__ == '__main__':
    prog = app(0)
    prog.MainLoop()

