from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QHeaderView
from qclickablelabel import QClickableLabel
import sys
from ui import Ui_mainWindow 
import os
import pyodbc
import hashlib
import base64
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem, QIcon
import sys
import requests
from io import BytesIO
import math
from PyQt5.QtWidgets import QAbstractItemView,QToolTip
from PyQt5.QtCore import QThreadPool, QDate
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
import traceback
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "tomjubb.mma.companion"
)

#Configuring DPI settings so the UI isn't all messed up
print("#Configuring DPI settings so the UI isn't all messed up")
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"

#Dealing with exceptions
def exceptHook(exc_type,exc,tb):
    msg = "".join(traceback.format_exception(exc_type, exc, tb))
    QtWidgets.QMessageBox.critical(None, "Error", msg)
sys.excepthook=exceptHook

#Main Window
print("Main Window")
class MainWindow(QtWidgets.QMainWindow): 
    def __init__(self):
        self.pendingEdits={} #table, key, column
        global fightsTablePendingEdits
        fightsTablePendingEdits=[]
        super().__init__()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("MMA Companion")
        iconPath = os.path.join(os.path.dirname(__file__), "..", "Assets", "icon.ico")
        self.setWindowIcon(QIcon(iconPath))
        #modify fighter globals
        global modFighterCurrentId
        modFighterCurrentId = None
        #odds calc globals
        global rightComboActive
        global oddsComboCurrentWeightClass
        global leftComboActive
        global selectedA
        global selectedB
        global updatingTables
        rightComboActive = False
        leftComboActive = False
        updatingTables = False
        oddsComboCurrentWeightClass = None
        selectedA=0
        selectedB=0
        #leaderboard globals
        global leaderboardCurrentId
        leaderboardCurrentId = None
        #fighter profile globals
        global userProfileFighterID
        #options globals
        global eventClickedIndex
        global beltClickedIndex
        
        #init options elements
        self.ui.optionsReturnButton.clicked.connect(lambda:self.loadModifyFighter())
        self.ui.addBeltsButton.clicked.connect(lambda:self.addBelt())
        self.ui.deleteBeltsButton.clicked.connect(lambda:self.deleteBelt())
        self.ui.deleteEventsButton.clicked.connect(lambda:self.deleteEvent())
        self.ui.addEventsButton.clicked.connect(lambda:self.addEvent())
        self.ui.beltsTable.clicked.connect(lambda index:self.beltClicked(index))
        self.ui.eventsTable.clicked.connect(lambda index:self.eventClicked(index))
        self.ui.optionsSubmitButton.clicked.connect(lambda index:(self.submitEdits(self.ui.eventsTable),self.submitEdits(self.ui.beltsTable)))

        #init fighterProfiles elements
        print("#init fighterProfiles elements")
        self.ui.fighterProfileReturn.clicked.connect(lambda:self.initLeaderboard())
        self.ui.fighterProfilePositiveRating.clicked.connect(lambda:self.voteApproval(userProfileFighterID,1))
        self.ui.fighterProfileNegativeRating.clicked.connect(lambda:self.voteApproval(userProfileFighterID,0))
        
        #init leaderboard elements
        print("#init leaderboard elements")
        self.ui.leaderboardOddsCheckerButton.clicked.connect(lambda:self.initOddsCalc())
        self.ui.leaderboardManageListButton.clicked.connect(lambda: self.loadModifyFighter())
        self.ui.leaderboardTableView.clicked.connect(lambda index:self.leaderboardLoadFighterData(index))
        self.ui.leaderboardSearchButton.clicked.connect(lambda:self.leaderboardSearchFighter())
        self.ui.leaderboardTableView.doubleClicked.connect(self.showProfileUser)
        self.ui.leaderboardTableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        
        #init odds calculator elements
        self.ui.fighterAComboBox.currentIndexChanged[int].connect(lambda index: self.comboBoxesChanged(index,"A"))
        self.ui.fighterBComboBox.currentIndexChanged[int].connect(lambda index: self.comboBoxesChanged(index,"B"))
            
        #init login elements
        print("#init login elements")
        self.ui.loginLoginButton.clicked.connect(lambda:self.accounts.login(self))
        self.ui.loginSignUpButton.clicked.connect(lambda:self.accounts.signUp(self))
            
        #init modifyFighter elements
        print("#init modifyFighter elements")
        self.ui.modifyFighterImagePreview.clicked.connect(lambda:self.modifyFightersPreviewImage())
        self.ui.modifyFighterSubmit.clicked.connect(lambda:self.submitFighterFights())
        self.ui.modifyFighterReturn.clicked.connect(lambda:self.loadModifyFighter())
        self.ui.modifyFighterAddFight.clicked.connect(lambda:self.modifyFighterAddFight())
        self.ui.modifyFighterDeleteFight.clicked.connect(lambda:self.modifyFighterDeleteFight())
        ##setup modifyfighter tooltip system
        self.fighterNameMap = dict(self.connect("SELECT FighterID, Name FROM Fighters;", "many", None) or []) #dictionary so i don't have to repeatedly call for the sql
        self.ui.modifyFighterFightsTable.setMouseTracking(True)
        self.ui.modifyFighterFightsTable.entered.connect(self.fighterIdTooltip)
        

        
        #init modifyFighterList elements
        print("#init modifyFighterList elements")
        self.ui.modifyViewAsUserButton.clicked.connect(lambda:self.initLeaderboard())
        self.ui.modifyAddFighterButton.clicked.connect(lambda:self.addFighter())
        self.ui.modifyDeleteFighterButton.clicked.connect(lambda:self.deleteFighter())
        self.ui.modifyFighterListTable.clicked.connect(lambda index:self.modFighterLoadFighterData(index))
        self.ui.modifyFighterListSearchButton.clicked.connect(lambda:self.modFighterSearchFighter())
        self.ui.modifyFighterListTable.doubleClicked.connect(self.showProfileAdmin)
        self.ui.modifyOptionsButton.clicked.connect(lambda:self.initOptions())
            
        #init oddsPredictor elements
        print("#init oddsPredictor elements")
        self.ui.OddsReturn.clicked.connect(lambda:self.initLeaderboard())
        self.ui.OddsClearButton.clicked.connect(lambda:self.resetComboBoxes())
        self.ui.CalculateButton.clicked.connect(lambda:self.submitOddsCalc())
        
        #init fighter profile elements
           
            
        #init survey elements
        print("#init survey elements")
        #Ko stars in survey
        self.ui.surveyStarSub1.clicked.connect(lambda:self.starClicked("sub",0))
        self.ui.surveyStarSub2.clicked.connect(lambda:self.starClicked("sub",1))
        self.ui.surveyStarSub3.clicked.connect(lambda:self.starClicked("sub",2))
        self.ui.surveyStarSub4.clicked.connect(lambda:self.starClicked("sub",3))
        self.ui.surveyStarSub5.clicked.connect(lambda:self.starClicked("sub",4))
        
        # Ko stars
        self.ui.surveyStarKo1.clicked.connect(lambda:self.starClicked("ko",0))
        self.ui.surveyStarKo2.clicked.connect(lambda:self.starClicked("ko",1))
        self.ui.surveyStarKo3.clicked.connect(lambda:self.starClicked("ko",2))
        self.ui.surveyStarKo4.clicked.connect(lambda:self.starClicked("ko",3))
        self.ui.surveyStarKo5.clicked.connect(lambda:self.starClicked("ko",4))
        
        # Dec stars
        self.ui.surveyStarDec1.clicked.connect(lambda:self.starClicked("dec",0))
        self.ui.surveyStarDec2.clicked.connect(lambda:self.starClicked("dec",1))
        self.ui.surveyStarDec3.clicked.connect(lambda:self.starClicked("dec",2))
        self.ui.surveyStarDec4.clicked.connect(lambda:self.starClicked("dec",3))
        self.ui.surveyStarDec5.clicked.connect(lambda:self.starClicked("dec",4))
        
        self.ui.surveySubmitButton.clicked.connect(lambda:self.surveySubmit())
        
        self.navigate(3)
    
    #SQL subroutines
    ##Execute SQL statements
    def connect(self, statementSQL,queryType,params):
        print(statementSQL)
        try:
            cs = (
                r"Driver={SQL Server};"
                r"Server=THE_MACHINE\SQLEXPRESS;"
                r"Database=Database;"
                r"Trusted_Connection=yes;"
            )
            
            cnx = pyodbc.connect(cs)
            print("Connected")
            if cnx is not None:
                cursor = cnx.cursor()
                if params is not None:
                    cursor.execute(statementSQL,params)
                else:
                    cursor.execute(statementSQL) 
                if queryType == "one":
                    row=cursor.fetchone()
                    return row
                if queryType == "many":
                    rows=cursor.fetchall()
                    return rows
                if queryType == "none" or queryType=="None":
                    cnx.commit()
                    print("Commited")
                    return None
                else:
                    QtWidgets.QMessageBox.critical(None, "SQL Error", "Querytype out of bounds")
            else:
                print("SQL ERROR: cnx is none")
        except pyodbc.DatabaseError as err:
            QtWidgets.QMessageBox.critical(None, "SQL Error", str(err))
        finally:
            if 'cnx' in locals() and cnx:
                cnx.close()
            print("Connection Closed")
    
    #Table subroutines
    ##Model a table off of a query
    def genTable(self,query,headers,table,dbTableName=None,pkColName=None,dbCols=None,isFightsTable=None):
        statementSQL,queryType,params = query
        rows=self.connect(statementSQL,queryType,params)
        if not rows:
            rows=[]
        model = QStandardItemModel()
        model.blockSignals(True)
        model._tableName=dbTableName  
        model._pkCol=pkColName       
        model._dbCols=dbCols
        model.setHorizontalHeaderLabels(headers)
        if dbTableName is not None and pkColName is not None and dbCols is not None:
            model.itemChanged.connect(lambda item:self.recordEdit(item))
        if isFightsTable is not None:
            model.itemChanged.connect(lambda item:self.recordFightsEdit(item))
        for row in rows:
            item = [QStandardItem(str(field)) for field in row]
            model.appendRow(item)
        table.setModel(model)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(30)
        header.setDefaultAlignment(Qt.AlignCenter)
        model.blockSignals(False)
    ##Return row and column and data of clicked table   
    def onTableClick(self,table,index):
        row=index.row()
        column=index.column()
        value=index.data()
        return([row,column,value])
    ##Record edit on editable table
    def recordEdit(self,item):
        model=item.model()
        row=item.row()
        col=item.column()
        if not hasattr(model,"_tableName") or model._tableName is None:
            return
        if not hasattr(model,"_pkCol") or model._pkCol is None:
            return
        if not hasattr(model,"_dbCols") or model._dbCols is None:
            return
        if col == 0:
            return
        primaryKey=model.item(row,0).text()    
        columnName=model._dbCols[col]           
        newValue=item.text()                   
        if newValue=="" or newValue=="None":
            newValue=None
        self.pendingEdits[(model._tableName,model._pkCol,primaryKey,columnName)]=newValue
        print("Pending edit:",model._tableName,primaryKey,columnName,newValue)
    ##Submit edits 
    def submitEdits(self,table):
        print("Submit edits")
        model=table.model()
        if model is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No model")
            return
        if not hasattr(model,"_tableName") or model._tableName is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No model tablename")
            return
        if not hasattr(model,"_pkCol") or model._pkCol is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No model pk columns")
            return
        keysToApply=[]
        for key in list(self.pendingEdits.keys()):
            tableName,pkCol,primaryKey,columnName=key
            if tableName==model._tableName and pkCol==model._pkCol:
                keysToApply.append(key)
        for key in keysToApply:
            tableName,pkCol,primaryKey,columnName=key
            newValue=self.pendingEdits[key]
            query="UPDATE "+tableName+" SET "+columnName+"=? WHERE "+pkCol+"=?"
            self.connect(query,"none",(newValue,primaryKey))
            del self.pendingEdits[key]
    ##record fighter fights table edit
    def recordFightsEdit(self,item):
        global fightsTablePendingEdits
        row=item.row()
        col=item.column()
        fightsTablePendingEdits.append([row,col])
        print("Adding to edit queue:",row,col)
    ##submit fighter fights table edit
    def submitFighterFights(self):
        global fighterId
        global fightsTablePendingEdits
        model=self.ui.modifyFighterFightsTable.model()
        if model is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No model")
            return
        #Edits arranged into their columns
        columns=[
            ["FighterFightsID","FighterFights"],#profile ff id 
            ["FightID","FighterFights"],#prof fight id
            ["FighterFightsID","FighterFights"],#opp fighterfights id
            ["FighterID","FighterFights"],#opponent id 
            ["EventID","Fights"],#Event id
            ["Result","FighterFights"],#fight result
            ["Method","Fights"],#fight end method
            ["EndRound","Fights"],#fight endround
            ["EndTime","Fights"],#fight endtime
            ["Title","Fights"],#fight endtitle
        ]
        rowCount=model.rowCount()
        for edit in range(len(fightsTablePendingEdits)):
            row=fightsTablePendingEdits[edit][0]
            col=fightsTablePendingEdits[edit][1]
            if col < 2:
                QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Col is out of range")
                return
            cell = model.item(row, col)
            value = None if cell is None else cell.text()
            if row is None or col is None or value is None:
                QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Row/Col/Value is None")
                return
            model.item(row,col).text()
            if columns[col][1]=="FighterFights": #Updates opponent and result data
                print("Setting value",value,"to",columns[col][1])
                key=model.item(row,0).text()
                print("FighterFights Key is ",key)
                opponentKey=model.item(row,2).text()
                opponentFighterFightsKey=model.item(row,3).text()
                FighterFightsKey=model.item(row,0).text()
                oppositeResult=self.oppositeResult(str(value))
                if opponentKey is None or opponentKey=="" or opponentKey=="None":
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No opponent key")
                if oppositeResult is None:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Bad result")
                if columns[col][0]=="FighterID":
                    #updates opponent on fighterfights
                    #firstly, remove the old opponent's fighterfights
                    FighterFights=self.connect("SELECT * FROM FighterFights WHERE FighterFights.FighterFightsID = ?;","one",FighterFightsKey)
                    for record in FighterFights:
                        if record is None:
                            record="None"
                    query="""
                    DELETE FROM FighterFights
                    WHERE FighterFights.FighterFightsID = ?
                    """
                    self.connect(query,"none",(opponentFighterFightsKey,))
                    #then add the new opponent's fighterfights
                    query="""
                    INSERT INTO FighterFights
                    VALUES (?,?,?,?)
                    """
                    self.connect(query,"none",(value,FighterFights[1],self.oppositeResult(FighterFights[2]),FighterFights[3]))
                if columns[col][0]=="Result":
                    #updates result for both fighterfights tables
                    #firstly, update the result for the profile fighter
                    query="""
                    UPDATE FighterFights
                    SET Result=?
                    WHERE FighterFightsID=?;
                    """
                    self.connect(query,"none",(value,key))
                    #then, also update the opponent fighter's result
                    query="""
                    UPDATE FighterFights
                    SET Result=?
                    WHERE FighterFightsID=?;
                    """
                    self.connect(query,"none",(oppositeResult,opponentKey))
                else:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No parametised operation for fighterfights edit")       
            elif columns[col][1]=="Fights": #Updates fight data
                print("Setting value",columns[col][0],"to",value)
                key=model.item(row,1).text()
                print("Fight Key is ",key)
                query="UPDATE Fights SET "+columns[col][0]+"=? WHERE FightID=?;"
                self.connect(query,"none",(value,key))
        query="""DECLARE @FighterID INT = ?;
        SELECT
        FighterFights.FighterFightsID AS [FighterFightsID],
        FighterFights.FightID         AS [FightID],
        (
        SELECT TOP 1 FighterFights.FighterFightsID
        FROM FighterFights
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
        ) AS [OpponentFighterFightsID],
        (
        SELECT TOP 1 FighterFights.FighterID
        FROM FighterFights
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
        ) AS [OpponentID],
        Fights.EventID,
        FighterFights.Result AS [Result],
        Fights.Method AS [Method],
        Fights.EndRound AS [Round],
        CONVERT(char(5), Fights.EndTime, 108) AS [Time],
        Fights.Title
        FROM FighterFights
        JOIN Fights  ON Fights.FightID  = FighterFights.FightID
        JOIN Events  ON Events.EventID  = Fights.EventID
        WHERE FighterFights.FighterID = @FighterID
        ORDER BY Fights.FightID DESC;
        """
        self.genTable((query,"many",(fighterId)),headers=["FighterFightsID","FightID","OppFFID","Opponent ID","EventID","Result","Method","Round","Time","Title"],table=self.ui.modifyFighterFightsTable,isFightsTable=True)
        self.submitProfile
         
    #Request Subroutines
    ##Load image and pixmap onto an element
    def loadImage(self,url,element,mode,imagePath):
        element.clear()
        print("loadimage")
        pixmap = QPixmap()
        #validation for request
        try:
            if mode == "File":
                if imagePath is None:
                    print("Image path is none")
                    return
                imagePath = os.path.join(os.path.dirname(__file__), "..", "Assets", imagePath)
                imagePath = os.path.abspath(imagePath)
                print(imagePath)
                pixmap = QPixmap(imagePath)
                if pixmap.isNull():
                    print("Default image won't load")
                pixmap.load(imagePath)
            else:  
                if url is None:
                    print("Url is none")
                    return
                headers = {
                    "User-Agent": "TJ CompSci tomjubb29@gmail.com"
                }
                response=requests.get(url, headers=headers ,timeout=5)
                #validate to image
                if "image" not in response.headers.get("Content-Type", ""):
                    print("not an image:", url)
                    element.clear()
                    return
                image=response.content
                pixmap = QPixmap()
                pixmap.loadFromData(image) 
            #scaling pixmap to make it not look stupid
            if not pixmap.isNull():
                elementSize = element.size()
                scaledPixmap = pixmap.scaled(
                    elementSize, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                    )
                element.setPixmap(scaledPixmap)
                element.setScaledContents(False)
                element.setAlignment(Qt.AlignCenter)
            else:
                element.clear()
                
        except requests.RequestException as e:    
            print(e)
            element.clear()
    
    #levenshtien search subroutines
    ##Get levenshtien distance
    def levenshtien(self,string1,string2):
        length1,length2=len(string1),len(string2)
        #Make the shorter one go first
        if length1 > length2:
            string1,string2=string2,string1
            length1,length2=length2,length1
        #Figure out the first row of the matrix
        currentRow = list(range(length1+1))
        #look at each character of string2
        for i in range(1,length2+1):
            lastRow, currentRow = currentRow, [i] + [0] * length1
            #Look at each character in string1
            for j in range(1, length1+1):
                #figure out costs of inserting deleting and substituting
                add=lastRow[j]+1
                delete=currentRow[j - 1]+1
                substitute=lastRow[j-1]
                change=substitute
                #Add one if the characters are different
                if string1[j-1] != string2[i-1]:
                    change=change+1
                #find minimum cost
                currentRow[j]=min(add,delete,change)
        #Last of the last element is the levenshtein distance
        return currentRow[length1]
    ##Return levenshtein distances of the fighter table so you can sort it
    def tableDistances(self,searchTerm):
        rows= self.connect("SELECT FighterID, Name FROM Fighters;","many",None)
        distances=[]
        #assign each row a distance
        for i in range(len(rows)):
            current=rows[i][1]
            distance=self.levenshtien(current,searchTerm)
            distances.append((rows[i][0],distance))
        #sort the list by ascending distance
        distances.sort(key=lambda x:x[1])   
        return distances
                                          
    #Navigation subroutines 
    def navigate(self,page):
        global activePage
        activePage = page
        pages=[
        self.ui.fighterProfiles,
        self.ui.leaderboard,
        self.ui.login,
        self.ui.modifyFighter,
        self.ui.modifyFighterList,
        self.ui.oddsPredictor,
        self.ui.survey,
        self.ui.options]
        print("Navigating to",pages[page-1])
        for i in range(len(pages)):
           pages[i].hide()
        pages[page-1].show() 
     
    #Star selection subroutines
    def starClicked(self,row,number):
        global subOpinion
        global koOpinion
        global decOpinion
        subStars=[self.ui.surveyStarSub1, self.ui.surveyStarSub2, self.ui.surveyStarSub3, self.ui.surveyStarSub4, self.ui.surveyStarSub5]
        koStars=[self.ui.surveyStarKo1, self.ui.surveyStarKo2, self.ui.surveyStarKo3, self.ui.surveyStarKo4, self.ui.surveyStarKo5]
        decStars=[self.ui.surveyStarDec1, self.ui.surveyStarDec2, self.ui.surveyStarDec3, self.ui.surveyStarDec4, self.ui.surveyStarDec5]
        print("Star Clicked",str(row),str(number))
        if row == "sub":
             stars = subStars
        elif row == "ko":
             stars = koStars
        elif row == "dec":
             stars = decStars
        for i in range(5):
            if i <= number:
                imagePath = os.path.join(os.path.dirname(__file__), "..", "Assets", "FilledStar.png")
                imagePath = os.path.abspath(imagePath)
                stars[i].setPixmap(QPixmap(imagePath))
            else:
                imagePath = os.path.join(os.path.dirname(__file__), "..", "Assets", "BlankStar.png")
                imagePath = os.path.abspath(imagePath)
                stars[i].setPixmap(QPixmap(imagePath))
        if row == "sub":
            subOpinion = number + 1
            print(subOpinion)
        elif row == "ko":
            koOpinion = number + 1
            print(koOpinion)
        elif row == "dec":
            decOpinion = number + 1
            print(decOpinion)
    
    #Result allocation subroutine 
    def oppositeResult(self,result):
        if result == "W":
            return "L"
        elif result == "L":
            return "W"
        elif result == "Red":
            return "Blue"
        elif result == "Blue":
            return "Red"
        elif result == "NC":
            return "NC"
        else:
            QtWidgets.QMessageBox.critical(None, "Opposite result error", "No counterpart found (wrong corner or result)")   
            
    #Login and survey subroutines
    class accounts():
        def __init__(self):
            pass
        #Login subroutine
        def login(self):
            print("Login")
            #Fetch login details from textboxes
            username = self.ui.loginUsernameText.toPlainText()
            password = self.ui.loginPasswordText.toPlainText()
            #Check for username and also fetch login details
            row=self.connect("SELECT * FROM dbo.Users WHERE Username = ?","one",(username,))
            if row:
                storedPassword=row[0]
                print(storedPassword)
                #Split hash and salt and then decode them
                base64salt,base64hash=storedPassword.split(":") 
                decodedHash= base64.b64decode(base64hash)
                decodedSalt = base64.b64decode(base64salt)
                #Recompute Hash and then compare to check password is correct
                newHash = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode(),
                    decodedSalt,
                    100000
                )       
                if decodedHash != newHash:
                    print("Incorrect Password")
                    self.ui.loginError.setText("Incorrect Password")
                    return
                if decodedHash == newHash:
                    print("Login success")
                    #set session variables and navigate to wherever is necessary depending on whether the user is an admin or not
                    global isAdmin
                    global usernameToken
                    isAdmin=row[6]
                    usernameToken=username
                    if isAdmin==1:
                        print("Login as admin")
                        self.loadModifyFighter()
                    else:
                        print("Login as regular")
                        self.initLeaderboard()
            else:
                print("Account doesn't exist") 
                self.ui.loginError.setText("Account doesn't exist")    
        #Signup subroutine
        def signUp(self):
            #Bring username from textboxes
            username = self.ui.loginUsernameText.toPlainText()
            password = self.ui.loginPasswordText.toPlainText()
            #Check if username is already in use
            usernameCheck=self.connect("SELECT 1 FROM dbo.Users WHERE Username = ?","one",(username,))
            if usernameCheck:
                print("Username already exists")
                self.ui.loginError.setText("Username already exists")
                return
            print("signUp")
            #Salt and hash password
            salt = os.urandom(16)
            hash_bytes = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt,
                100000          
            )
            base64salt = base64.b64encode(salt).decode()
            base64hash = base64.b64encode(hash_bytes).decode()
            hashedPassword=f"{base64salt}:{base64hash}"
            print(username)
            print(hashedPassword)
            #Insert new account into Users table
            self.connect("INSERT INTO Users (Username, HashedPassword,SubOpinion,KoOpinion,DecisionOpinion,isAdmin) VALUES (?, ?,1,1,1,0)","none",(username, hashedPassword))     
            #Set session variables and navigate to leaderboard
            global isAdmin
            global usernameToken
            usernameToken = username
            isAdmin = 0
            self.navigate(7) 
    def surveySubmit(self):
        print(subOpinion,decOpinion,koOpinion)
        self.connect("UPDATE dbo.Users SET SubOpinion = ?, KoOpinion = ?, DecisionOpinion = ? WHERE Username=?;","none",(subOpinion,koOpinion,decOpinion,usernameToken))
        self.initLeaderboard()  
    
    #ModifyFighter Subroutines  
    ##initialise the page
    def loadModifyFighter(self):
        self.genTable(("SELECT * FROM Fighters","many",None),["FighterID","Name","Weight Class","Birthdate","Gym","Rating","Volatility","Rating Deviation","Image URL"],self.ui.modifyFighterListTable)
        self.navigate(5)
    ##add fighter   
    def addFighter(self):
        placeholderFighter = ('John Smith','Lightweight','1987-01-01','Gym',1500,350,200)
        self.connect("INSERT INTO Fighters (Name, WeightClass, Birthdate, Gym, EloRating, Volatility, RatingDeviation) VALUES (?, ?, ?, ?, ?, ?, ?)","none",placeholderFighter)
        self.loadModifyFighter()
    ##load data of fighter onto right part of gui when part of table is clicked
    def modFighterLoadFighterData(self,index):
        TotalLosses=0
        TotalWins=0
        TotalDraws=0
        global modFighterCurrentId
        model = self.ui.modifyFighterListTable.model()
        row, col, value = self.onTableClick(self.ui.modifyFighterListTable, index)
        modFighterCurrentId = model.item(row,0).text()
        fighterData=self.connect("SELECT * FROM Fighters WHERE FighterID=?;","one",(modFighterCurrentId,))
        self.ui.modifyFighterListName.setText(fighterData[1])
        #Load image
        if fighterData[8]:
            print("loadimage")
            self.loadImage(fighterData[8],self.ui.modifyFighterListImage,None,None)
        else:
            self.loadImage(None,self.ui.modifyFighterListImage,"File","defaultpfp.png")
        #Load record
        fighterFightData=self.connect("SELECT * FROM FighterFights WHERE FighterID=?;","many",(modFighterCurrentId,))
        print(fighterFightData)
        for i in range(len(fighterFightData)):
            if fighterFightData[i][3] == "Loss":
                TotalLosses=TotalLosses+1
            if fighterFightData[i][3] == "Win":
                TotalWins=TotalWins+1
            if fighterFightData[i][3] == "Draw":
                TotalDraws=TotalDraws+1
        self.ui.modifyFighterListLosses.setText(str(TotalLosses))
        self.ui.modifyFighterListWins.setText(str(TotalWins))
        self.ui.modifyFighterListDraws.setText(str(TotalDraws))
    #delete fighter
    def deleteFighter(self):
        print("Delete fighterID",modFighterCurrentId)
        if modFighterCurrentId:
            self.connect("DELETE FROM Fighters WHERE FighterID=?;","none",(modFighterCurrentId,))
            self.loadModifyFighter()
    #searchforfighter
    def modFighterSearchFighter(self):
        model=self.ui.modifyFighterListTable.model()
        searchTerm = self.ui.modifyFighterListSearchText.toPlainText()
        distances = self.tableDistances(searchTerm)
        newTable = []
        for fighterID, distance in distances:
            rowData=[]
            for row in range(model.rowCount()):
                item=model.item(row,0)
                if item and int(item.text()) == fighterID:
                    for col in range(model.columnCount()):
                        cell=model.item(row,col)
                        rowData.append(cell.text() if cell else "")
                    break
            newTable.append(rowData)        
        model.clear() 
        model.setColumnCount(len(newTable[0]) if newTable else 0) 
        for row,rowData in enumerate(newTable):
            for col, value in enumerate(rowData):
                model.setItem(row,col,QStandardItem(value))
            
    #Odds Predictor
    ##Initialise combo boxes
    def initComboBoxes(self):
        global updatingTables
        global leftComboActive
        global rightComboActive
        global oddsComboCurrentWeightClass
        currentA = self.ui.fighterAComboBox.currentData()
        currentB = self.ui.fighterBComboBox.currentData()
        self.clearComboBoxes()
        comboBoxes=[self.ui.fighterAComboBox,self.ui.fighterBComboBox]
        currentSelections=[currentA,currentB]
        comboBoxes[0].blockSignals(True)
        comboBoxes[1].blockSignals(True)
        self.clearComboBoxes()
        if oddsComboCurrentWeightClass:
            query=("SELECT FighterID, Name FROM Fighters WHERE WeightClass=?;", "many", (oddsComboCurrentWeightClass,))
        else:
            query = ("SELECT FighterID, Name FROM Fighters;", "many", None)
        fighterList = self.connect(query[0],query[1],query[2])
        if not fighterList:
            fighterList = []
        for i in range(2):
            for fighterID,fighterName in fighterList:
                comboBoxes[i].addItem(fighterName,fighterID)
                index = comboBoxes[i].findData(currentSelections[i])
                if index != -1:
                    comboBoxes[i].setCurrentIndex(index)
        comboBoxes[0].blockSignals(False)
        comboBoxes[1].blockSignals(False)
        if activePage != 6:
            self.navigate(6)
    ##When combo boxes change    
    def comboBoxesChanged(self, index, box):
        global updatingTables
        global oddsComboCurrentWeightClass
        if updatingTables == True:
            print("Already updating-returning from comboboxeschanged...")
            return
        updatingTables = True 
        comboBoxes = [self.ui.fighterAComboBox, self.ui.fighterBComboBox]
        currentID = None
        if box == "A":
            currentID = comboBoxes[0].currentData()
        elif box == "B":
            currentID = comboBoxes[1].currentData()
        if currentID is not None:
            currentFighter = self.connect("SELECT * FROM Fighters WHERE FighterID=?", "one", (currentID,))
            if currentFighter is not None:
                oddsComboCurrentWeightClass = currentFighter[2] 
                print("current weight class:", oddsComboCurrentWeightClass)
            else:
                oddsComboCurrentWeightClass = None 
        else:
            oddsComboCurrentWeightClass = None 
        self.initComboBoxes() 
        updatingTables = False
        fighterAID = self.ui.fighterAComboBox.currentData()
        fighterBID = self.ui.fighterBComboBox.currentData()
        if fighterAID is not None:
            fighterAdata = self.connect("SELECT * FROM Fighters WHERE FighterID=?", "one", (fighterAID,))
            fighterAurl = fighterAdata[8] if fighterAdata and len(fighterAdata) > 8 else None
            print(fighterAurl)
            if fighterAurl is not None:
                fighterAurl = fighterAdata[8] 
                self.loadImage(fighterAurl,self.ui.fighterABox,None,None)
            else:
                self.ui.fighterABox.clear()
        else:
            self.ui.fighterABox.clear()
        if fighterBID is not None:
            fighterBdata = self.connect("SELECT * FROM Fighters WHERE FighterID=?", "one", (fighterBID,))
            fighterBurl = fighterBdata[8] if fighterBdata and len(fighterBdata) > 8 else None
            print(fighterBurl)
            if fighterBurl is not None:
                fighterBurl = fighterBdata[8] 
                self.loadImage(fighterBurl,self.ui.fighterBBox,None,None)
            else:
                self.ui.fighterBBox.clear()
        else:
            self.ui.fighterBBox.clear()
    ##Clears combo boxes     
    def clearComboBoxes(self):
        self.ui.fighterAtAdvantage.setText("Fighter At Advantage")
        self.ui.ProbResult.setText("0%")
        self.ui.fighterAComboBox.clear()
        self.ui.fighterBComboBox.clear()
    ##Resets combo boxes
    def resetComboBoxes(self):
        global oddsComboCurrentWeightClass
        global updatingTables
        updatingTables=True
        oddsComboCurrentWeightClass=None
        self.ui.fighterAComboBox.blockSignals(True)
        self.ui.fighterBComboBox.blockSignals(True)
        self.clearComboBoxes()
        query = ("SELECT FighterID, Name FROM Fighters;", "many", None)
        fighterList = self.connect(query[0], query[1], query[2])
        if not fighterList:
            fighterList = []
        for fighterID, fighterName in fighterList:
            self.ui.fighterAComboBox.addItem(fighterName, fighterID)
            self.ui.fighterBComboBox.addItem(fighterName, fighterID)
        self.ui.fighterAComboBox.setCurrentIndex(-1)
        self.ui.fighterBComboBox.setCurrentIndex(-1)
        self.ui.fighterABox.clear()
        self.ui.fighterBBox.clear()
        self.ui.fighterAComboBox.blockSignals(False)
        self.ui.fighterBComboBox.blockSignals(False)
        updatingTables = False  
    ##init odds calc
    def initOddsCalc(self):
        self.initComboBoxes()
        self.navigate(6)
    ##Submit odds calculation and display  
    def submitOddsCalc(self): 
        fighterAID = self.ui.fighterAComboBox.currentData()
        fighterBID = self.ui.fighterBComboBox.currentData()
        fighterAData = self.connect("SELECT * FROM Fighters WHERE FighterID=?", "one", (fighterAID,))
        fighterBData = self.connect("SELECT * FROM Fighters WHERE FighterID=?", "one", (fighterBID,))
        fighterAElo = fighterAData[5]
        fighterBElo = fighterBData[5]
        fighterAName = fighterAData[1]
        fighterBName = fighterBData[1]
        probA = fighterAElo / (fighterAElo+fighterBElo)
        probA=round(probA,2)
        probA=probA*100
        if probA > 50:
            #A dominant
            probA=str(probA)
            probA=probA+"%"
            stringToDisplay=fighterAName+" at favourite"
            self.ui.fighterAtAdvantage.setText(stringToDisplay)
            self.ui.ProbResult.setText(probA)
            
        elif probA < 50:
            #B dominant
            probA=100-probA
            probA=str(probA)
            probA=probA+"%"
            stringToDisplay=fighterBName+" at favourite"
            self.ui.fighterAtAdvantage.setText(stringToDisplay)
            self.ui.ProbResult.setText(probA)   
        else:
            self.ui.fighterAtAdvantage.setText("Pick 'em odds")
            self.ui.ProbResult.setText("50%")    
      
    #Leaderboard subproblems
    ##Initialize leaderboard
    def initLeaderboard(self):
        self.genTable(("SELECT FighterID,Name,WeightClass,Birthdate,Gym FROM Fighters","many",None),["FighterID","Name","Weight Class","Birthdate","Gym"],self.ui.leaderboardTableView)
        self.ui.leaderboardTableView.setColumnHidden(0, True)
        self.ui.leaderboardFighterBelts.setText("")
        self.ui.leaderboardFighterRecord.setText("")
        self.navigate(2)
    ##Load fighter data from leaderboard
    def leaderboardLoadFighterData(self,index):
        TotalLosses=0
        TotalWins=0
        TotalDraws=0
        global leaderboardCurrentId
        model = self.ui.leaderboardTableView.model()
        row, col, value = self.onTableClick(self.ui.leaderboardTableView, index)
        leaderboardCurrentId = model.item(row,0).text()
        fighterData=self.connect("SELECT * FROM Fighters WHERE FighterID=?;","one",(leaderboardCurrentId,))
        self.ui.leaderboardFighterName.setText(fighterData[1])
        #Load image
        if fighterData[8]:
            print("loadimage")
            self.loadImage(fighterData[8],self.ui.leaderboardImage,None,None)
        else:
            self.loadImage(None,self.ui.leaderboardImage,"File","defaultpfp.png")
        #Load record
        fighterFightData=self.connect("SELECT * FROM FighterFights WHERE FighterID=?;","many",(leaderboardCurrentId,))
        print(fighterFightData)
        for i in range(len(fighterFightData)):
            if fighterFightData[i][3] == "Loss":
                TotalLosses=TotalLosses+1
            if fighterFightData[i][3] == "Win":
                TotalWins=TotalWins+1
            if fighterFightData[i][3] == "Draw":
                TotalDraws=TotalDraws+1
        record=str(TotalWins)+"-"+str(TotalDraws)+"-"+str(TotalLosses)
        self.ui.leaderboardFighterRecord.setText(record)
        beltsList=self.connect("SELECT * FROM Belts WHERE FighterID=(SELECT FighterID FROM Fighters WHERE FighterID=?);","many",(leaderboardCurrentId,))
        if beltsList:
            beltsText="Belts: "
            for row in beltsList:
                beltsText=beltsText+str(row[1])+" "
            self.ui.leaderboardFighterBelts.setText(beltsText)
        else:
            self.ui.leaderboardFighterBelts.setText("")
    ##Search for fighters in the leaderboard
    def leaderboardSearchFighter(self):
        model=self.ui.leaderboardTableView.model()
        searchTerm = self.ui.leaderboardFighterSearch.toPlainText()
        headers = ["FighterID", "Name", "Weight Class", "Birthdate", "Gym"]
        distances = self.tableDistances(searchTerm)
        newTable = []
        for fighterID, distance in distances:
            rowData=[]
            for row in range(model.rowCount()):
                item=model.item(row,0)
                if item and int(item.text()) == fighterID:
                    for col in range(model.columnCount()):
                        cell=model.item(row,col)
                        rowData.append(cell.text() if cell else "")
                    break
            newTable.append(rowData)        
        model.clear()  
        model.setColumnCount(len(headers)) 
        model.setHorizontalHeaderLabels(headers)
        for row,rowData in enumerate(newTable):
            for col, value in enumerate(rowData):
                model.setItem(row,col,QStandardItem(value)) 
        self.ui.leaderboardTableView.setColumnHidden(0, True)
      
    #Admin-side profile subroutines
    ##Initialise fighter proifle page on admin side
    def showProfileAdmin(self,index):
        global fighterId
        fighterId = index.siblingAtColumn(0).data() 
        print("display profile of fighterID "+fighterId)
        fighterData=self.connect("SELECT * FROM Fighters WHERE FighterId=?","one",(fighterId))
        print("fighterdata:"+str(fighterData))
        self.ui.modifyFighterTitle.setText("Editing Fighter:"+str(fighterData[1]))
        self.ui.modifyFighterName.setPlainText(str(fighterData[1]))
        self.ui.modifyFighterGym.setPlainText(str(fighterData[4]))
        self.ui.modifyFighterImageLink.setPlainText(str(fighterData[8]))
        self.loadImage(fighterData[8],self.ui.modifyFighterImage,None,None)
        #deal with weight classes
        self.ui.modifyFighterWeightclass.setCurrentText(fighterData[2])
        #deal with birthday
        date = QDate.fromString(fighterData[3], "yyyy-MM-dd")
        self.ui.modifyFighterBirthday.setDate(date)
        #display fights
        query="""DECLARE @FighterID INT = ?;
        SELECT
        FighterFights.FighterFightsID AS [FighterFightsID],
        FighterFights.FightID         AS [FightID],
        (
        SELECT TOP 1 FighterFights.FighterFightsID
        FROM FighterFights
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
        ) AS [OpponentFighterFightsID],
        (
        SELECT TOP 1 FighterFights.FighterID
        FROM FighterFights
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
        ) AS [OpponentID],
        Fights.EventID,
        FighterFights.Result AS [Result],
        Fights.Method AS [Method],
        Fights.EndRound AS [Round],
        CONVERT(char(5), Fights.EndTime, 108) AS [Time],
        Fights.Title
        FROM FighterFights
        JOIN Fights  ON Fights.FightID  = FighterFights.FightID
        JOIN Events  ON Events.EventID  = Fights.EventID
        WHERE FighterFights.FighterID = @FighterID
        ORDER BY Fights.FightID DESC;
        """
        self.genTable((query,"many",(fighterData[0])),headers=["FighterFightsID","FightID","OppFFID","Opponent ID","EventID","Result","Method","Round","Time","Title"],table=self.ui.modifyFighterFightsTable,isFightsTable=True)
        self.ui.modifyFighterFightsTable.setColumnHidden(0, True)
        self.ui.modifyFighterFightsTable.setColumnHidden(1, True)
        self.ui.modifyFighterFightsTable.setColumnHidden(2, True)
        #display belts
        beltsList=self.connect("SELECT * FROM Belts WHERE FighterID=(SELECT FighterID FROM Fighters WHERE FighterID=?);","many",(fighterData[0],))
        if beltsList:
            beltsText="Belts (Change in options): "
            for row in beltsList:
                beltsText=beltsText+str(row[1])+" "
            self.ui.modifyFighterBelts.setText(beltsText)
        else:
            self.ui.modifyFighterBelts.setText("Belts (Change in options):None")
        self.navigate(4)
    ##Preview image button
    def modifyFightersPreviewImage(self):
        url=self.ui.modifyFighterImageLink.toPlainText()
        self.loadImage(url,self.ui.modifyFighterImage,None,None)
    ##Submit button
    def submitProfile(self):
        global fighterId
        nameToSubmit=self.ui.modifyFighterName.toPlainText()
        gymToSubmit=self.ui.modifyFighterGym.toPlainText()
        weightClassToSubmit=self.ui.modifyFighterWeightclass.currentText()
        dateToSubmit=self.ui.modifyFighterBirthday.date().toString("yyyy-MM-dd")
        imageLinkToSubmit=self.ui.modifyFighterImageLink.toPlainText()
        if imageLinkToSubmit=="None":
            imageLinkToSubmit=None
        self.connect("UPDATE Fighters SET Name=?,WeightClass=?,Birthdate=?,Gym=?,ImageURL=? WHERE FighterID=?","none",(nameToSubmit,weightClassToSubmit,dateToSubmit,gymToSubmit,imageLinkToSubmit,fighterId))    ##Tooltip system on fights list
    def fighterIdTooltip(self, index):
        if not index.isValid():
            QToolTip.hideText()
            return
        table = self.sender()  
        if index.column() != 0:
            QToolTip.hideText()
            return
        try:
            fighterId = int(index.data())
        except (TypeError, ValueError):
            QToolTip.hideText()
            return
        name = self.fighterNameMap.get(fighterId)
        if name:
            QToolTip.showText(QCursor.pos(), name, table)
        else:
            QToolTip.hideText()
    ##Add fight button
    def modifyFighterAddFight(self):
        global fighterId
        print("Add fight")
        query="""
        DECLARE @FightID INT;
DECLARE @FighterID INT=?;
INSERT INTO dbo.Fights (EventID, Method, EndRound, EndTime, Title)
VALUES (NULL, 'KO', 1, '00:04:00', 'Main Event');
SET @FightID = SCOPE_IDENTITY();
INSERT INTO dbo.FighterFights (FightID, FighterID, Corner, Result)
VALUES
(@FightID, @FighterID, 'Red',  'W');"""
        self.connect(query,"None",(fighterId))
        query="""DECLARE @FighterID INT = ?;
        SELECT
        FighterFights.FighterFightsID AS [FighterFightsID],
        FighterFights.FightID         AS [FightID],
        (
        SELECT TOP 1 FighterFights.FighterFightsID
        FROM FighterFights
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
        ) AS [OpponentFighterFightsID],
        (
        SELECT TOP 1 FighterFights.FighterID
        FROM FighterFights
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
        ) AS [OpponentID],
        Fights.EventID,
        FighterFights.Result AS [Result],
        Fights.Method AS [Method],
        Fights.EndRound AS [Round],
        CONVERT(char(5), Fights.EndTime, 108) AS [Time],
        Fights.Title
        FROM FighterFights
        JOIN Fights  ON Fights.FightID  = FighterFights.FightID
        JOIN Events  ON Events.EventID  = Fights.EventID
        WHERE FighterFights.FighterID = @FighterID
        ORDER BY Fights.FightID DESC;
        """
        self.genTable((query,"many",(fighterId)),headers=["FighterFightsID","FightID","OppFFID","Opponent ID","EventID","Result","Method","Round","Time","Title"],table=self.ui.modifyFighterFightsTable,isFightsTable=True)   
    #Delete fight
    def modifyFighterDeleteFight(self):
        global modFighterSelected
        query="""DECLARE @FightID INT = ?;
        DELETE FROM dbo.FighterFights
        WHERE FightID = @FightID;
        DELETE FROM dbo.Fights
        WHERE FightID = @FightID;"""
        self.connect(query,"none",(modFighterCurrentId))
        query="""DECLARE @FighterID INT = ?;
        SELECT
        FighterFights.FighterFightsID AS [FighterFightsID],
        FighterFights.FightID         AS [FightID],
        (
        SELECT TOP 1 FighterFights.FighterFightsID
        FROM FighterFights
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
        ) AS [OpponentFighterFightsID],
        (
        SELECT TOP 1 FighterFights.FighterID
        FROM FighterFights
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
        ) AS [OpponentID],
        Fights.EventID,
        FighterFights.Result AS [Result],
        Fights.Method AS [Method],
        Fights.EndRound AS [Round],
        CONVERT(char(5), Fights.EndTime, 108) AS [Time],
        Fights.Title
        FROM FighterFights
        JOIN Fights  ON Fights.FightID  = FighterFights.FightID
        JOIN Events  ON Events.EventID  = Fights.EventID
        WHERE FighterFights.FighterID = @FighterID
        ORDER BY Fights.FightID DESC;
        """
        self.genTable((query,"many",(fighterId)),headers=["FighterFightsID","FightID","OppFFID","Opponent ID","EventID","Result","Method","Round","Time","Title"],table=self.ui.modifyFighterFightsTable,isFightsTable=True)  

    ##Select fight 
    def modifyFighterSelectFight(self,index):
        global modFighterSelected
        modFighterCurrentId=index.siblingAtColumn(1).data() 
    
    #User-side profile subroutines
    ##Intialise fighter profile page on user side
    def showProfileUser(self,index):
        global userProfileFighterID
        self.ui.nodatamessage.hide()
        fighterId = index.siblingAtColumn(0).data() 
        userProfileFighterID=fighterId
        print("display profile of fighterID "+fighterId)
        fighterData=self.connect("SELECT * FROM Fighters WHERE FighterId=?","one",(fighterId))
        print("fighterdata:"+str(fighterData))
        self.ui.fighterProfileName.setText(str(fighterData[1]))
        self.loadImage(fighterData[8],self.ui.fighterProfileImage,None,None)
        query="""DECLARE @FighterID INT = ?;

SELECT
    (
        SELECT TOP 1 Fighters.Name
        FROM FighterFights
        JOIN Fighters ON Fighters.FighterID = FighterFights.FighterID
        WHERE FighterFights.FightID = Fights.FightID
          AND FighterFights.FighterID <> @FighterID
    ) AS [Opponent],
    Events.Name AS [Event],
    FighterFights.Result AS [Result],
    Fights.Method AS [Method],
    Fights.EndRound AS [Round],
    CONVERT(char(5), Fights.EndTime, 108) AS [Time]
FROM FighterFights
JOIN Fights ON Fights.FightID = FighterFights.FightID
JOIN Events ON Events.EventID = Fights.EventID
WHERE FighterFights.FighterID = @FighterID
ORDER BY Fights.FightID DESC;"""
        self.genTable((query,"many",(fighterData[0])),["Opponent Name","Event Name","Result","Method","Round","Time"],self.ui.fighterProfileFights,isFightsTable=True)
        #Piechart-Figure out totals (sub/ko/dec)
        totalWinsQuery="""SELECT COUNT(*)
FROM FighterFights
JOIN Fights ON Fights.FightID = FighterFights.FightID
WHERE FighterFights.FighterID = ?
  AND FighterFights.Result = 'Win'
  AND Fights.Method = ?;"""
        winsBreakdown=[self.connect(totalWinsQuery,"one",(fighterData[0],"Submission")),self.connect(totalWinsQuery,"one",(fighterData[0],"KO/TKO")),self.connect(totalWinsQuery,"one",(fighterData[0],"Decision"))]
        totalWinsQuery="""SELECT COUNT(*)
FROM FighterFights
JOIN Fights ON Fights.FightID = FighterFights.FightID
WHERE FighterFights.FighterID = ?
  AND FighterFights.Result = 'Loss'
  AND Fights.Method = ?;"""
        lossBreakdown=[self.connect(totalWinsQuery,"one",(fighterData[0],"Submission")),self.connect(totalWinsQuery,"one",(fighterData[0],"KO/TKO")),self.connect(totalWinsQuery,"one",(fighterData[0],"Decision"))]
        #methods breakdown (winssub/winsko/winsdec/losssub/lossko/lossdec)
        methodsBreakdown=winsBreakdown+lossBreakdown
        print(methodsBreakdown)
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        labels = ["Submission Wins", "KO Wins", "Decision Wins","Submission Losses","KO Losses","Decision Losses"]
        colourIndex=["darkorange","orange","gold","lightsteelblue","skyblue","slateblue"]
        sizes = [methodsBreakdown[0][0],methodsBreakdown[1][0],methodsBreakdown[2][0],methodsBreakdown[3][0],methodsBreakdown[4][0],methodsBreakdown[5][0]]
        print(sizes)
        newLabels = []
        newSizes = []
        newColourIndex = []
        for i in range(len(sizes)):
            if sizes[i] > 0:
                newLabels.append(labels[i])
                newColourIndex.append(colourIndex[i])
                newSizes.append(sizes[i])
        labels = newLabels
        sizes = newSizes
        colourIndex = newColourIndex
        all0=True
        for term in sizes:
            if term != 0:
                all0=False
        print(sizes)
        if len(sizes) is None or all0==True:
            self.ui.nodatamessage.show()
        ax.pie(sizes, labels=labels, autopct="%1.0f%%", colors=colourIndex)
        ax.axis("equal")  # keeps it circular
        layout = self.ui.fighterGraph.layout()
        #clear the layout if i have used it before
        if layout is not None:     
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
        else:
            layout = QVBoxLayout(self.ui.fighterGraph)
        layout.addWidget(canvas)
        canvas.setStyleSheet("background: transparent;")
        canvas.setAttribute(Qt.WA_TranslucentBackground, True)
        self.ui.fighterGraph.setStyleSheet("background: transparent;")
        fig.patch.set_alpha(0)      
        ax.set_facecolor("none") 
        canvas.draw()
        #deal with rating
        self.displayApproval(userProfileFighterID)
        self.navigate(1)
    ##Display approval percentage
    def displayApproval(self,fighterID):  
        print("Display Approvals")
        ratingTotal=self.connect("SELECT COUNT(*) FROM Approvals WHERE FighterID=?;","one",(fighterID))
        positiveTotal=self.connect("SELECT COUNT(*) FROM Approvals WHERE FighterID=? AND Rating=1;","one",(fighterID))
        if ratingTotal[0] == 0 or positiveTotal[0] == 0:
            rating=0
        else:
            rating=(positiveTotal[0]/ratingTotal[0])*100
        self.ui.fighterApprovalRating.setText(str(int(rating))+"%")
        print(rating)  
    ##Approval votes
    def voteApproval(self,fighterID,rating):
        global usernameToken
        rating=1 if int(rating) == 1 else 0
        user=self.connect("SELECT userId FROM Users where Username=?;","one",(usernameToken))
        if not user:
            QtWidgets.QMessageBox.critical(None, "Error", "No user found")
            return
        userID=user[0]
        existing=self.connect("SELECT Rating FROM Approvals WHERE UserID=? AND FighterID=?","one",(userID,fighterID))
        if not existing:
            self.connect("INSERT INTO Approvals VALUES (?,?,?)","none",(userID,fighterID,rating))
        if existing:
            self.connect("UPDATE Approvals SET Rating=? WHERE UserID=?","none",(rating,userID))
        self.displayApproval(fighterID)
        
    #Options subroutines
    ##Initialize options
    def initOptions(self):
        self.genTable(("SELECT * FROM Belts","many",None),["Belt ID","Name","Holder ID"],self.ui.beltsTable,"Belts","BeltID",["BeltID","WeightClass","FighterID"])
        self.genTable(("SELECT * FROM Events","many",None),["Event ID","Name","Location","Date"],self.ui.eventsTable,"Events","EventID",["EventID","Name","Location","Date"])
        self.navigate(8)
    #Belt clicked
    def beltClicked(self,index):
        global beltClickedIndex
        beltClickedIndex=index.siblingAtColumn(0).data() 
    ##Add belt
    def addBelt(self):
        self.connect("INSERT INTO Belts VALUES (?,1)","none",("Blank Belt",))
        self.genTable(("SELECT * FROM Belts","many",None),["Belt ID","Title","Holder ID"],self.ui.beltsTable)
        print("Add belt")
    ##Delete belt
    def deleteBelt(self):
        global beltClickedIndex
        print("Delete belt")
        if beltClickedIndex is not None:
            self.connect("DELETE FROM Belts WHERE BeltID=?","none",(beltClickedIndex,))
            self.genTable(("SELECT * FROM Belts","many",None),["Belt ID","Title","Holder ID"],self.ui.beltsTable)
    #Event clicked
    def eventClicked(self,index):
        global eventClickedIndex
        eventClickedIndex=index.siblingAtColumn(0).data() 
    ##Add event
    def addEvent(self):
        self.connect("INSERT INTO Events (Name,Location,Date) VALUES (?,?,?)","none",("name","location","1984-02-02"))
        self.genTable(("SELECT * FROM Events","many",None),["Event ID","Name","Location","Date"],self.ui.eventsTable)        
        print("Add event")
    ##Delete event
    def deleteEvent(self):
        global eventClickedIndex
        print("Delete event")
        if eventClickedIndex is not None:
            self.connect("DELETE FROM Events WHERE EventID=?","none",(eventClickedIndex,))
            self.genTable(("SELECT * FROM Events","many",None),["Event ID","Name","Location","Date"],self.ui.eventsTable)  
    ##Auto-assign belts
    def autoAssignBelts(self):
        print("auto assign belts")
    ##Import from UFC
    def importFromUFC(self):
        print("Import from UFC")
        
#Show the Window
print("Show the Window")
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    iconPath = os.path.join(os.path.dirname(__file__), "..", "Assets", "icon.ico")
    app.setWindowIcon(QIcon(iconPath)) 
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
