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
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem
import sys
import requests
from io import BytesIO
import math

#Configuring DPI settings so the UI isn't all messed up
print("#Configuring DPI settings so the UI isn't all messed up")
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"

#Setting how clickable labels work

#Main Window
print("Main Window")
class MainWindow(QtWidgets.QMainWindow): 
    def __init__(self):
        super().__init__()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
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

        #init fighterProfiles elements
        print("#init fighterProfiles elements")
        
        #init leaderboard elements
        print("#init leaderboard elements")
        self.ui.leaderboardOddsCheckerButton.clicked.connect(lambda:self.initOddsCalc())
        self.ui.leaderboardManageListButton.clicked.connect(lambda: self.loadModifyFighter())
        self.ui.leaderboardTableView.clicked.connect(lambda index:self.leaderboardLoadFighterData(index))
        self.ui.leaderboardSearchButton.clicked.connect(lambda:self.leaderboardSearchFighter())
        
        #init odds calculator elements
        self.ui.fighterAComboBox.currentIndexChanged[int].connect(lambda index: self.comboBoxesChanged(index,"A"))
        self.ui.fighterBComboBox.currentIndexChanged[int].connect(lambda index: self.comboBoxesChanged(index,"B"))
            
        #init login elements
        print("#init login elements")
        self.ui.loginLoginButton.clicked.connect(lambda:self.accounts.login(self))
        self.ui.loginSignUpButton.clicked.connect(lambda:self.accounts.signUp(self))
            
        #init modifyFighter elements
        print("#init modifyFighter elements")
            
            
        #init modifyFighterList elements
        print("#init modifyFighterList elements")
        self.ui.modifyViewAsUserButton.clicked.connect(lambda:self.initLeaderboard())
        self.ui.modifyAddFighterButton.clicked.connect(lambda:self.addFighter())
        self.ui.modifyDeleteFighterButton.clicked.connect(lambda:self.deleteFighter())
        self.ui.modifyFighterListTable.clicked.connect(lambda index:self.modFighterLoadFighterData(index))
        self.ui.modifyFighterListSearchButton.clicked.connect(lambda:self.modFighterSearchFighter())
            
        #init oddsPredictor elements
        print("#init oddsPredictor elements")
        self.ui.OddsReturn.clicked.connect(lambda:self.navigate(2))
        self.ui.OddsClearButton.clicked.connect(lambda:self.resetComboBoxes())
        self.ui.CalculateButton.clicked.connect(lambda:self.submitOddsCalc())
        
            
            
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
    
    #SQL subroutines
    ##Execute SQL statements
    def connect(self, statementSQL,queryType,params):
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
                if queryType == "none":
                    cnx.commit()
                    print("Commited")
                    return None
        except pyodbc.DatabaseError as err:
            print(err)
        finally:
            if 'cnx' in locals() and cnx:
                cnx.close()
            print("Connection Closed")
    
    #Table subroutines
    ##Model a table off of a query
    def genTable(self,query,headers,table):
        statementSQL,queryType,params = query
        rows=self.connect(statementSQL,queryType,params)
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(headers)
        for row in rows:
            item = [QStandardItem(str(field)) for field in row]
            model.appendRow(item)
        table.setModel(model)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(30)
        header.setDefaultAlignment(Qt.AlignCenter)
    ##Return row and column and data of clicked table   
    def onTableClick(self,table,index):
        row=index.row()
        column=index.column()
        value=index.data()
        return([row,column,value])
    
    #Request Subroutines
    ##Load image and pixmap onto an element
    def loadImage(self,url,element,mode,imagePath):
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
        self.ui.survey]
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
        
        
    #init odds calc
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
        
#Show the Window
print("Show the Window")
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
