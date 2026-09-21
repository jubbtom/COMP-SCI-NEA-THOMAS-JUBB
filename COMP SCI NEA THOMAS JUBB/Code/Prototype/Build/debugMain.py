
import base64
import ctypes
from datetime import datetime, date
import hashlib
import math
import os
print("#Configuring DPI settings so the UI isn't all messed up")
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"
import re
import sys
import time
import traceback
from io import BytesIO
import pyodbc
import requests
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "tomjubb.mma.companion"
)
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt,QDate,QObject,QRunnable,QThreadPool,pyqtSignal,pyqtSlot
from PyQt5.QtGui import QCursor, QIcon, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QAbstractItemView,QApplication,QLabel,QHeaderView,QMainWindow,QMessageBox,QPushButton,QToolTip,QVBoxLayout,QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qclickablelabel import QClickableLabel
from ui import Ui_mainWindow

#Dealing with exceptions
def exceptHook(exc_type,exc,tb):
    msg = "".join(traceback.format_exception(exc_type, exc, tb))
    QtWidgets.QMessageBox.critical(None, "Error", msg)
sys.excepthook=exceptHook

#Main Window
print("Main Window")
class MainWindow(QtWidgets.QMainWindow):  
    def __init__(self):
        self.pendingEdits={} #formatted as table, key, column
        self.fightsTablePendingEdits=[]
        super().__init__()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
        self.threadpool = QThreadPool()
        print(f"maximum {self.threadpool.maxThreadCount()} threads")
        self.setWindowTitle("MMA Companion")
        iconPath = os.path.join(os.path.dirname(__file__), "..", "Assets", "icon.ico")
        self.setWindowIcon(QIcon(iconPath))
        #modify fighter 
        self.modFighterCurrentId = None
        #odds calc 
        self.rightComboActive = False
        self.leftComboActive = False
        self.updatingTables = False
        self.oddsComboCurrentWeightClass = None
        self.selectedA=0
        self.selectedB=0
        #leaderboard 
        self.leaderboardCurrentId = None
        #fighter profile 
        self.userProfileFighterID = None
        #options 
        self.eventClickedIndex = None
        self.beltClickedIndex = None
        #survey 
        self.newAccount = None
        self.subOpinion=1
        self.koOpinion=1
        self.decOpinion=1
        #Other session vars
        self.activePage=None
        self.isAdmin=None
        self.usernameToken=None
        self.fighterId=None
                
        #init options elements
        self.ui.optionsReturnButton.clicked.connect(lambda:self.loadModifyFighter())
        self.ui.addBeltsButton.clicked.connect(lambda:self.addBelt())
        self.ui.deleteBeltsButton.clicked.connect(lambda:self.deleteBelt())
        self.ui.deleteEventsButton.clicked.connect(lambda:self.deleteEvent())
        self.ui.addEventsButton.clicked.connect(lambda:self.addEvent())
        self.ui.beltsTable.clicked.connect(lambda index:self.beltClicked(index))
        self.ui.eventsTable.clicked.connect(lambda index:self.eventClicked(index))
        self.ui.optionsSubmitButton.clicked.connect(lambda index:(self.submitEdits(self.ui.eventsTable),self.submitEdits(self.ui.beltsTable)))
        self.ui.optionsAutoAssign.clicked.connect(lambda: self.autoAssignBelts())

        #init fighterProfiles elements
        print("#init fighterProfiles elements")
        self.ui.fighterProfileReturn.clicked.connect(lambda:self.initLeaderboard())
        self.ui.fighterProfilePositiveRating.clicked.connect(lambda:self.voteApproval(self.userProfileFighterID,1))
        self.ui.fighterProfileNegativeRating.clicked.connect(lambda:self.voteApproval(self.userProfileFighterID,0))
        self.ui.fighterProfileFights.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        #init leaderboard elements
        print("#init leaderboard elements")
        self.ui.leaderboardOddsCheckerButton.clicked.connect(lambda:self.initOddsCalc())
        self.ui.leaderboardManageListButton.clicked.connect(lambda: self.loadModifyFighter())
        self.ui.leaderboardTableView.clicked.connect(lambda index:self.leaderboardLoadFighterData(index))
        self.ui.leaderboardSearchButton.clicked.connect(lambda:self.leaderboardSearchFighter())
        self.ui.leaderboardTableView.doubleClicked.connect(self.showProfileUser)
        self.ui.leaderboardTableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ui.leaderboardSurveyButton.clicked.connect(lambda:self.initSurvey(False))

        
        #init odds calculator elements
        self.ui.fighterAComboBox.currentIndexChanged[int].connect(lambda index: self.comboBoxesChanged(index,"A"))
        self.ui.fighterBComboBox.currentIndexChanged[int].connect(lambda index: self.comboBoxesChanged(index,"B"))
            
        #init login elements
        print("#init login elements")
        self.ui.loginLoginButton.clicked.connect(self.login)
        self.ui.loginSignUpButton.clicked.connect(self.signUp)
            
        #init modifyFighter elements
        print("#init modifyFighter elements")
        self.ui.modifyFighterImagePreview.clicked.connect(lambda:self.modifyFightersPreviewImage())
        self.ui.modifyFighterSubmit.clicked.connect(lambda:self.submitFighterFights())
        self.ui.modifyFighterReturn.clicked.connect(lambda:self.loadModifyFighter())
        self.ui.modifyFighterAddFight.clicked.connect(lambda:self.modifyFighterAddFight())
        self.ui.modifyFighterDeleteFight.clicked.connect(lambda:self.modifyFighterDeleteFight())
        self.ui.modifySubmitButton.clicked.connect(lambda:self.updateEloRatings())
        ##setup modifyfighter tooltip system
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
                #Select query mode (fetch one/ fetch all/ fetch none which is for updating and deleting things from tables)
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
                    QtWidgets.QMessageBox.critical(None, "SQL Error", "Querytype of query"+str(statementSQL)+"out of bounds")
            else:
                print("SQL ERROR: cnx is none")
        except pyodbc.DatabaseError as err:
            QtWidgets.QMessageBox.critical(None, "SQL Error", "Database rejection.")
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
        #Stop model signals so edits aren't messed up
        model.blockSignals(True)
        model._tableName=dbTableName  
        model._pkCol=pkColName       
        model._dbCols=dbCols
        model.setHorizontalHeaderLabels(headers)
        if dbTableName is not None and pkColName is not None and dbCols is not None:
            model.itemChanged.connect(lambda item:self.recordEdit(item))
        if isFightsTable:
            model.itemChanged.connect(lambda item:self.recordFightsEdit(item))
        for row in rows:
            item = [QStandardItem(str(field)) for field in row]
            model.appendRow(item)
        table.setModel(model)
        table.setSortingEnabled(True)
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
    ##Record edit on editable tables (events table and belts table)
    def recordEdit(self,item):
        model=item.model()
        row=item.row()
        col=item.column()
        #Verify that the edit has all of the components present to be saved into the database later
        if not hasattr(model,"_tableName") or model._tableName is None:
            QtWidgets.QMessageBox.critical(None, "Record Edits Error", "No tablename attribute")
            return
        if not hasattr(model,"_pkCol") or model._pkCol is None:
            QtWidgets.QMessageBox.critical(None, "Record Edits Error", "No primary key attribute")
            return
        if not hasattr(model,"_dbCols") or model._dbCols is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No column attribute")
            return
        if col == 0:
            QtWidgets.QMessageBox.critical(None, "Record Edits Error", "IDs are not editable. This edit won't be saved.")
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
        #Verify that the model is there with all of its features
        if model is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No model")
            return
        if not hasattr(model,"_tableName") or model._tableName is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No model tablename")
            return
        if not hasattr(model,"_pkCol") or model._pkCol is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No model pk columns")
            return
        #Set up each key
        keysToApply=[]
        for key in list(self.pendingEdits.keys()):
            tableName,pkCol,primaryKey,columnName=key
            if tableName==model._tableName and pkCol==model._pkCol:
                keysToApply.append(key)
        for key in keysToApply:
            tableName, pkCol, primaryKey, columnName = key
            newValue = self.pendingEdits[key]
            #Belts title validation
            if tableName == "Belts" and columnName == "WeightClass":
                #Validate belts
                beltCheck = self.connect("SELECT COUNT(*) FROM Belts WHERE WeightClass=?","one",(newValue,))
                if newValue is None:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Pending edits is None")
                    self.initOptions()
                    return   
                else:
                    if not newValue.strip():
                            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Belt name is blank")
                            self.initOptions()
                            return    
                    if newValue=="RETIRED":
                            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Invalid Belt name")
                            self.initOptions()
                            return  
                    if len(newValue)>60:
                            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Belt name too long.")
                            self.initOptions()
                            return     
                    if beltCheck is not None:
                        if beltCheck[0] > 0:
                            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Belt already exists")
                            self.initOptions()
                            return
            #Belts fighter lookup check
            if tableName == "Belts" and columnName == "FighterID":
                FighterCheck = self.connect("SELECT FighterID FROM Belts WHERE FighterID=?","one",(newValue,))
                if FighterCheck == None:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Fighter doesn't exist.")
                    self.initOptions()
                    return    
            #Events Validation
            if tableName == "Events" and columnName in ["Name","Location","Date"]:
                eventRow = self.connect("SELECT Name, Location, Date FROM Events WHERE EventID=?","one",(primaryKey,))
                name, location, date = eventRow
                if columnName == "Name":
                    name = newValue
                    if not name.strip():
                        QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Event name is blank")
                        self.initOptions()
                        return   
                    if len(name) > 80:
                        QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Event name Too long")
                        self.initOptions()
                        return
                        
                if columnName == "Location":
                    location = newValue
                    if len(location) > 100:
                        QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Event location Too long")
                        self.initOptions()
                        return
                        
                if columnName == "Date":
                    date = newValue
                    #date validation
                    try:
                        eventDate=datetime.strptime(date, "%Y-%m-%d").date()
                        today = date.today()
                        if today < eventDate:
                            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Date can't be in the future")
                            self.initOptions()
                            return
                    except:
                        QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Date must be in YYYY-MM-DD format")
                        self.initOptions()
                        return
                #Event dupe check
                eventsCheck = self.connect("SELECT COUNT(*) FROM Events WHERE Name=? AND Location=? AND Date=? AND EventID<>?","one",(name, location, date,primaryKey,))
                if eventsCheck[0] > 0:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Event already exists")
                    self.initOptions()
                    return
            #Events format check
        #Apply each key
        for key in keysToApply:
            tableName,pkCol,primaryKey,columnName=key
            newValue=self.pendingEdits[key]
            query="UPDATE "+tableName+" SET "+columnName+"=? WHERE "+pkCol+"=?"
            self.connect(query,"none",(newValue,primaryKey))
            del self.pendingEdits[key]
    ##record fighter fights table edit
    def recordFightsEdit(self,item):
        row=item.row()
        col=item.column()
        self.fightsTablePendingEdits.append([row,col])
        print("Adding to edit queue:",row,col)
    ##submit fighter fights table edit
    def submitFighterFights(self):
        self.fighterId
        #Check for model existing
        model = self.ui.modifyFighterFightsTable.model()
        if model is None:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No model")
            return
        #List out all of the unique edits
        uniqueEdits = list({(r, c) for r, c in self.fightsTablePendingEdits})
        self.fightsTablePendingEdits.clear()

        for (row, col) in uniqueEdits:
            # ignore hidden columns
            if col < 3:
                continue
            #Check cells
            cell = model.item(row, col)
            value = None if cell is None else cell.text()
            if value is not None and (value.strip() == "" or value.strip() == "None"):
                value = None
            profileFFID = model.item(row, 0).text()  # hidden
            fightID     = model.item(row, 1).text()  # hidden
            #Opponent ID checking 
            if col == 3:
                newOppID = value
                # allow clearing opponent
                if newOppID is None:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "OpponentID doesn't exist")
                    continue
                # must be int and not same as profile fighter
                try:
                    newOppID_int = int(newOppID)
                except ValueError:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "OpponentID must be a number.")
                    continue
                #must exist
                opponentCount=self.connect("""SELECT COUNT(*) FROM Fighters WHERE FighterID=?;""","one",(newOppID_int))
                if opponentCount[0]!=1:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "OpponentID doesn't exist")
                    continue
                if str(newOppID_int) == str(self.fighterId):
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "OpponentID can't equal the current fighter.")
                    continue

                # opponent result should mirror profile result (col 5)
                profileResult = model.item(row, 5).text() if model.item(row, 5) else None
                oppResult = None
                if profileResult not in (None, "", "None"):
                    oppResult = self.oppositeResult(profileResult)

                # remove any existing opponent rows for that fight, then insert the new one
                self.connect(
                    "DELETE FROM dbo.FighterFights WHERE FightID=? AND FighterID<>?;",
                    "none",
                    (fightID, self.fighterId)
                )
                self.connect(
                    "INSERT INTO dbo.FighterFights (FightID, FighterID, Corner, Result) VALUES (?, ?, NULL, ?);",
                    "none",
                    (fightID, newOppID_int, oppResult)
                )
                continue
            #Result
            if col == 5:
                newResult = value
                #lookup check
                if newResult != "L" and newResult != "W" and newResult != "NC":
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Incorrect method formatting (L or W or NC).")
                    continue
                # update profile fighterfights row
                self.connect(
                    "UPDATE dbo.FighterFights SET Result=? WHERE FighterFightsID=?;",
                    "none",
                    (newResult, profileFFID)
                )

                # update opponent row (if it exists)
                oppResult = None
                if newResult not in (None, "", "None"):
                    oppResult = self.oppositeResult(newResult)
                #Update fighterfights 
                self.connect(
                    "UPDATE dbo.FighterFights SET Result=? WHERE FightID=? AND FighterID<>?;",
                    "none",
                    (oppResult, fightID, self.fighterId)
                )
                continue
            #  4 EventID,  6 Method,  7 Round,  8 Time,  9 Title
            if col == 4:  # EventID
                if value is None:
                    eventVal = None
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Event ID missing")
                    continue
                else:
                    try:
                        eventVal = int(value)
                    except ValueError:
                        QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "EventID must be a number (or None).")
                        continue
                eventDate = self.connect( "SELECT TRY_CONVERT(date, [Date]) FROM Events WHERE EventID=?;","one",(eventVal,))[0]
                #Checking if the event actually exists (lookup validation)
                eventExists=self.connect("SELECT EventID FROM Events WHERE EventID=?","one",(eventVal))
                if eventExists==None:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "EventID must exist.")
                    continue
                #Checking if the event has already been fought on by the fighter
                eventAlready=self.connect("""SELECT COUNT(*) FROM Fights 
JOIN FighterFights ON FighterFights.FightID = Fights.FightID
WHERE Fights.EventID = ?
AND FighterFights.FighterID = ?;""","one",(eventVal,self.fighterId))
                if eventAlready[0] != 0:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Fighter ID "+str(self.fighterId)+" already has a fight on event "+str(eventVal))
                    continue
                #Checking if the fighter has fought more than 12 times per year
                eventTimes=self.connect("""SELECT COUNT(*) AS FightCountSameYear
FROM FighterFights
JOIN Fights  ON Fights.FightID = FighterFights.FightID
JOIN Events e  ON e.EventID = Fights.EventID
WHERE FighterFights.FighterID = ?
  AND YEAR(TRY_CONVERT(date, e.[Date])) = (
      SELECT YEAR(TRY_CONVERT(date, e2.[Date]))
      FROM Events e2
      WHERE e2.EventID = ?
  )
  AND TRY_CONVERT(date, e.[Date]) IS NOT NULL;""","one",(self.fighterId,eventVal))
                if eventTimes[0] >= 12:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Fighter ID "+str(self.fighterId)+" has an impossible number of fights (more than 12 per year)")
                    continue
                #Checking if a fighter hasn't fought for at least a week
                fightsGapCheck=self.connect("""SELECT Fights.FightID, Events.EventID, TRY_CONVERT(date, Events.[Date]) AS FightDate
                FROM FighterFights
                JOIN Fights  ON Fights.FightID = FighterFights.FightID
                JOIN Events  ON Events.EventID = Fights.EventID
                WHERE FighterFights.FighterID = ?
                AND Fights.FightID <> ?
                AND TRY_CONVERT(date, e.[Date]) IS NOT NULL
                AND ABS(DATEDIFF(day, TRY_CONVERT(date, Events.[Date]), ?)) < 7;""","one",(self.fighterId,fightID,eventDate))
                if fightsGapCheck and len(fightsGapCheck)>0:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Fighter ID "+str(self.fighterId)+" has fought less than a week ago.")
                    continue
                self.connect("UPDATE dbo.Fights SET EventID=? WHERE FightID=?;", "none", (eventVal, fightID))
                continue

            if col == 6:  # Method
                if value != "SUB" and value != "DEC" and value != "KO":
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Incorrect method formatting (SUB or DEC or KO).")
                    continue
                self.connect("UPDATE dbo.Fights SET Method=? WHERE FightID=?;", "none", (value, fightID))
                continue

            if col == 7:  # EndRound
                if value is None:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Endround doesn't exist")
                    continue
                else:
                    try:
                        roundVal = int(value)
                        if roundVal < 1 or roundVal > 5:
                            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Round must be in range 1-5")
                            continue
                    except ValueError:
                        QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Round must be a number.")
                        continue
                self.connect("UPDATE dbo.Fights SET EndRound=? WHERE FightID=?;", "none", (roundVal, fightID))
                continue

            if col == 8:  # EndTime 
                t = value
                if t is not None: #normalizing time
                    t=t.strip()
                    t = "00:0"+t
                #check format of time
                timeCompile = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$")
                if t is None or  bool(timeCompile.match(t.strip())) == False:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Endtime either formatted badly or doesn't exist. (Format M:SS)")
                    continue
                #check that fight is physically possible
                strippedT = datetime.strptime(t.strip(), "%H:%M:%S").time()
                if (strippedT.hour, strippedT.minute, strippedT.second) <= (0, 0, 1) or (strippedT.hour, strippedT.minute, strippedT.second) > (0, 5, 0):
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Endtime physically impossible. Check your data inputs.")
                    continue
                self.connect("UPDATE dbo.Fights SET EndTime=? WHERE FightID=?;", "none", (t, fightID))
                continue
            
            if col == 9:  # Title
                if len(value)>60:
                    QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Title length too long.")
                    continue
                self.connect("UPDATE dbo.Fights SET Title=? WHERE FightID=?;", "none", (value, fightID))
                continue
        self.submitProfile()
        # refresh table after edits
        self.showProfileAdmin(self.ui.modifyFighterListTable.currentIndex())
         
    #Request Subroutines
    ##Load image 
    def loadImage(self, url, element, mode, imagePath):
        element.clear()
        print("loadimage")
        #Load image from file
        if mode == "File":
            if imagePath is None:
                print("Image path is none")
                return
            fullPath = os.path.join(os.path.dirname(__file__), "..", "Assets", imagePath)
            fullPath = os.path.abspath(fullPath)
            pixmap = QPixmap(fullPath)
            self.applyPixmap(pixmap, element)
        #Load default profile picture
        else:  
            if url is None:
                print("Url is none")
                fullPath = os.path.join(os.path.dirname(__file__), "..", "Assets", "defaultpfp.png")
                fullPath = os.path.abspath(fullPath)
                pixmap = QPixmap(fullPath)
                self.applyPixmap(pixmap, element)
                return
            
            #Get background worker for the web request
            worker = ImageWorker(url, element)
            worker.signals.finished.connect(self.onImageDownloadFinished)
            worker.signals.error.connect(self.onImageDownloadError)
            self.threadpool.start(worker)
    #successful background download
    def onImageDownloadFinished(self, image_data, element):
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self.applyPixmap(pixmap, element)
    #failed background download
    def onImageDownloadError(self, error_msg, element):
        element.clear()
        print(f"Image Loader Error: {error_msg}")
        fullPath = os.path.join(os.path.dirname(__file__), "..", "Assets", "defaultpfp.png")
        fullPath = os.path.abspath(fullPath)
        pixmap = QPixmap(fullPath)
        self.applyPixmap(pixmap, element)
        element.clear()
        
    #handle the scaling and alignment
    def applyPixmap(self, pixmap, element):
        if not pixmap.isNull():
            elementSize = element.size()
            # Scaling pixmap to make it not look stupid
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
        #Normalise everything and build a list of distances
        rows= self.connect("SELECT FighterID, Name FROM Fighters;","many",None)
        if not rows:
            return []
        distances=[]
        searchTerm = str(searchTerm).lower().strip()
        for fighterID, fighterName in rows:
            currentName = str(fighterName).lower().strip()
            distance = self.levenshtien(currentName, searchTerm)
            distances.append((fighterID, distance, currentName))
        #Insertion sort
        for i in range(1, len(distances)):
            currentItem = distances[i]
            j = i - 1
            while j >= 0 and (
                distances[j][1] > currentItem[1] or
                (distances[j][1] == currentItem[1] and distances[j][2] > currentItem[2])
            ):
                distances[j + 1] = distances[j]
                j -= 1
            distances[j + 1] = currentItem
        #Remove other unnecessary fields to give off result table
        orderedDistances = []
        for fighterID, distance, fighterName in distances:
            orderedDistances.append((fighterID, distance))
        return orderedDistances
                
    #Navigation subroutines 
    def navigate(self,page):
        #Set active page
        self.activePage = page
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
        #Setting stars
        subStars=[self.ui.surveyStarSub1, self.ui.surveyStarSub2, self.ui.surveyStarSub3, self.ui.surveyStarSub4, self.ui.surveyStarSub5]
        koStars=[self.ui.surveyStarKo1, self.ui.surveyStarKo2, self.ui.surveyStarKo3, self.ui.surveyStarKo4, self.ui.surveyStarKo5]
        decStars=[self.ui.surveyStarDec1, self.ui.surveyStarDec2, self.ui.surveyStarDec3, self.ui.surveyStarDec4, self.ui.surveyStarDec5]
        print("Star Clicked",str(row),str(number))
        #Figure out row
        if row == "sub":
             stars = subStars
        elif row == "ko":
             stars = koStars
        elif row == "dec":
             stars = decStars
        else:
            return
        #Fill the stars
        for i in range(5):
            if i <= number:
                imagePath = os.path.join(os.path.dirname(__file__), "..", "Assets", "FilledStar.png")
                imagePath = os.path.abspath(imagePath)
                stars[i].setPixmap(QPixmap(imagePath))
            else:
                imagePath = os.path.join(os.path.dirname(__file__), "..", "Assets", "BlankStar.png")
                imagePath = os.path.abspath(imagePath)
                stars[i].setPixmap(QPixmap(imagePath))
        #Set opinion number
        if row == "sub":
            self.subOpinion = number + 1
            print(self.subOpinion)
        elif row == "ko":
            self.koOpinion = number + 1
            print(self.koOpinion)
        elif row == "dec":
            self.decOpinion = number + 1
            print(self.decOpinion)
        
            
    
    #Result allocation subroutine 
    def oppositeResult(self,result):
        #Get opposite result off of a qualitative fighter stat
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
    #Login subroutine
    def login(self):
        print("Login")
        #Fetch login details from textboxes
        username = self.ui.loginUsernameText.toPlainText()
        password = self.ui.loginPasswordText.toPlainText()
        if len(username) > 60:
            self.ui.loginError.setText("Username too long.")
            return
        if username.strip()=="" or password.strip()=="":
            self.ui.loginError.setText("Please enter a username and password.")
            return
        #Check for username and also fetch login details
        row=self.connect("SELECT * FROM dbo.Users WHERE Username = ?","one",(username,))
        if row:
            storedPassword=row[0]
            verificationResult=self.verifyPassword(password,storedPassword)   
            if verificationResult==False:
                print("Incorrect Password")
                self.ui.loginError.setText("Incorrect Password")
                return
            if verificationResult==True:
                print("Login success")
                #set session variables and navigate to wherever is necessary depending on whether the user is an admin or not
                self.isAdmin=row[6]
                self.usernameToken=username
                if self.isAdmin==1:
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
        hashedPassword=self.hashPassword(password)
        #Insert new account into Users table
        self.connect("INSERT INTO Users (Username, HashedPassword,SubOpinion,KoOpinion,DecisionOpinion,isAdmin,favouriteFighter) VALUES (?, ?,1,1,1,0,0)","none",(username, hashedPassword))     
        #Set session variables and navigate to leaderboard
        self.usernameToken = username
        self.isAdmin = 0
        self.initSurvey(False)
    #Verify password
    def verifyPassword(self,password,storedPassword):
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
            return False
        if decodedHash == newHash:
            return True
    #Hash password
    def hashPassword(self,password):
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
        return hashedPassword
    #Submit survey
    def surveySubmit(self):
        #Submit survey results
        print(self.subOpinion,self.decOpinion,self.koOpinion)
        favouriteFighter = self.ui.favouriteFighterCombo.currentData()
        self.connect("UPDATE dbo.Users SET SubOpinion = ?, KoOpinion = ?, DecisionOpinion = ?,favouriteFighter=? WHERE Username=?;","none",(self.subOpinion,self.koOpinion,self.decOpinion,favouriteFighter,self.usernameToken))
        self.initLeaderboard()
    #Initalise survey
    def initSurvey(self,new):
        self.newAccount=new
        self.ui.favouriteFighterCombo.clear()
        query=("SELECT FighterID, Name FROM Fighters;", "many", None)
        fighterList = self.connect(query[0],query[1],query[2])
        if not fighterList:
            fighterList = []
        for fighterID,fighterName in fighterList:
            self.ui.favouriteFighterCombo.addItem(fighterName,fighterID)
        self.navigate(7)
    
    #ModifyFighter Subroutines  
    ##initialise the page
    def loadModifyFighter(self):
        self.genTable(("SELECT FighterID,Name,WeightClass,Birthdate,Gym,EloRating,Volatility,RatingDeviation FROM Fighters","many",None),["FighterID","Name","Weight Class","Birthdate","Gym","Rating","Volatility","Rating Deviation"],self.ui.modifyFighterListTable)
        self.navigate(5)
    ##add fighter   
    def addFighter(self):
        placeholderFighter = ('John Smith','Lightweight','1987-01-01','Gym',1500,0.06,200,'5.10','6.0')
        self.connect("INSERT INTO Fighters (Name, WeightClass, Birthdate, Gym, EloRating, Volatility, RatingDeviation,Height,Reach) VALUES (?, ?, ?, ?, ?, ?, ?,?,?)","none",placeholderFighter)
        self.loadModifyFighter()
    ##load data of fighter onto right part of gui when part of table is clicked
    def modFighterLoadFighterData(self,index):
        #Load fighter table
        TotalLosses=0
        TotalWins=0
        TotalDraws=0
        model = self.ui.modifyFighterListTable.model()
        row, col, value = self.onTableClick(self.ui.modifyFighterListTable, index)
        self.modFighterCurrentId = model.item(row,0).text()
        fighterData=self.connect("SELECT * FROM Fighters WHERE FighterID=?;","one",(self.modFighterCurrentId,))
        self.ui.modifyFighterListName.setText(fighterData[1])
        #Load image
        if fighterData[8]:
            print("loadimage")
            self.loadImage(fighterData[8],self.ui.modifyFighterListImage,None,None)
        else:
            self.loadImage(None,self.ui.modifyFighterListImage,"File","defaultpfp.png")
        #Load record
        fighterFightData=self.connect("SELECT * FROM FighterFights WHERE FighterID=?;","many",(self.modFighterCurrentId,))
        print(fighterFightData)
        fighterFightData = self.connect(
    "SELECT Result FROM FighterFights WHERE FighterID=?;",
    "many",
    (self.modFighterCurrentId,) 
)
        for (result,) in fighterFightData:
            if result == "W":
                TotalWins += 1
            elif result == "L":
                TotalLosses += 1
            elif result == "D" or result == "NC":
                TotalDraws += 1
        self.ui.modifyFighterListLosses.setText(str(TotalLosses))
        self.ui.modifyFighterListWins.setText(str(TotalWins))
        self.ui.modifyFighterListDraws.setText(str(TotalDraws))
    #delete fighter
    def deleteFighter(self):
        print("Delete fighterID",self.modFighterCurrentId)
        if self.modFighterCurrentId:
            self.connect("DELETE FROM Fighters WHERE FighterID=?;","none",(self.modFighterCurrentId,))
            self.loadModifyFighter()
    #searchforfighter
    def modFighterSearchFighter(self):
        model=self.ui.modifyFighterListTable.model()
        searchTerm = self.ui.modifyFighterListSearchText.toPlainText()
        distances = self.tableDistances(searchTerm)
        newTable = []
        #Order table by least distant first
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
        #Populate model
        for row,rowData in enumerate(newTable):
            for col, value in enumerate(rowData):
                model.setItem(row,col,QStandardItem(value))
        model.setHorizontalHeaderLabels(["FighterID","Name","Weight Class","Birthdate","Gym","Rating","Volatility","Rating Deviation"])
            
    #Odds Predictor
    ##Initialise combo boxes
    def initComboBoxes(self):
        currentA = self.ui.fighterAComboBox.currentData()
        currentB = self.ui.fighterBComboBox.currentData()
        self.clearComboBoxes()
        comboBoxes=[self.ui.fighterAComboBox,self.ui.fighterBComboBox]
        currentSelections=[currentA,currentB]
        #Block signals for initialisation
        comboBoxes[0].blockSignals(True)
        comboBoxes[1].blockSignals(True)
        self.clearComboBoxes()
        #Bring up combo data
        if self.oddsComboCurrentWeightClass:
            query=("SELECT FighterID, Name FROM Fighters WHERE WeightClass=?;", "many", (self.oddsComboCurrentWeightClass,))
        else:
            query = ("SELECT FighterID, Name FROM Fighters;", "many", None)
        fighterList = self.connect(query[0],query[1],query[2])
        if not fighterList:
            fighterList = []
        #Populate box
        for i in range(2):
            for fighterID,fighterName in fighterList:
                comboBoxes[i].addItem(fighterName,fighterID)
                index = comboBoxes[i].findData(currentSelections[i])
                if index != -1:
                    comboBoxes[i].setCurrentIndex(index)
        comboBoxes[0].blockSignals(False)
        comboBoxes[1].blockSignals(False)
        #Let it be changed again
        if self.activePage != 6:
            self.navigate(6)
    ##When combo boxes change    
    def comboBoxesChanged(self, index, box):
        #Check is updating is happening already 
        if self.updatingTables == True:
            print("Already updating-returning from comboboxeschanged...")
            return
        self.updatingTables = True 
        comboBoxes = [self.ui.fighterAComboBox, self.ui.fighterBComboBox]
        currentID = None
        #Set current id of box
        if box == "A":
            currentID = comboBoxes[0].currentData()
        elif box == "B":
            currentID = comboBoxes[1].currentData()
        if currentID is not None:
            currentFighter = self.connect("SELECT * FROM Fighters WHERE FighterID=?", "one", (currentID,))
            if currentFighter is not None:
                self.oddsComboCurrentWeightClass = currentFighter[2] 
                print("current weight class:", self.oddsComboCurrentWeightClass)
            else:
                self.oddsComboCurrentWeightClass = None 
        else:
            self.oddsComboCurrentWeightClass = None 
        self.initComboBoxes() 
        self.updatingTables = False
        #Load images
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
        self.updatingTables=True
        self.oddsComboCurrentWeightClass=None
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
        self.updatingTables = False  
    ##init odds calc
    def initOddsCalc(self):
        self.initComboBoxes()
        self.navigate(6)
    ##Submit odds calculation and display  
    def submitOddsCalc(self): 
        fighterAID = self.ui.fighterAComboBox.currentData()
        fighterBID = self.ui.fighterBComboBox.currentData()
        print(fighterAID)
        print(fighterBID)
        if fighterAID == None or fighterBID == None:
            QtWidgets.QMessageBox.critical(None, "Odds calculation error", "Please make sure both fighters are selected.")
            return
        if fighterAID == fighterBID:
            QtWidgets.QMessageBox.critical(None, "Odds calculation error", "Please select two different fighters.")
            return
        fighterAData = self.connect("SELECT * FROM Fighters WHERE FighterID=?", "one", (fighterAID,))
        fighterBData = self.connect("SELECT * FROM Fighters WHERE FighterID=?", "one", (fighterBID,))
        fighterAElo = fighterAData[5]
        fighterBElo = fighterBData[5]
        fighterAName = fighterAData[1]
        fighterBName = fighterBData[1]
        #Glicko prob algorithm
        probA = 1.0 / (1.0 + 10 ** ((fighterBElo - fighterAElo) / 400.0))
        probA=probA*100
        probA=round(probA,2)
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
        ##Entertainment score calculation
        #Find average subs,kos,decs through whole roster
        totalFights=self.connect("""SELECT COUNT(*) FROM Fights;""","one",None)[0]
        totalSubs=self.connect("""SELECT COUNT(*) FROM Fights WHERE Method='SUB';""","one",None)[0]
        totalDecs=self.connect("""SELECT COUNT(*) FROM Fights WHERE Method='DEC';""","one",None)[0]
        totalKos=self.connect("""SELECT COUNT(*) FROM Fights WHERE Method='KO';""","one",None)[0]
        averageSubRate = (totalSubs / totalFights) * 100 if totalFights else 0
        averageKoRate = (totalKos / totalFights) * 100 if totalFights else 0
        averageDecRate = (totalDecs / totalFights) * 100 if totalFights else 0  
        #Find average subs,kos,decs rate for fighter A,map to prefs and make entertainment score
        fighterArray=[fighterAID,fighterBID]
        entertainmentRating=200
        for j in range(2):
            totalFights=self.connect("""SELECT COUNT(*) FROM FighterFights WHERE FighterID=?;""","one",(fighterArray[j],))
            if totalFights[0] == 0:
                entertainmentRating=50
                break
            totalSubs=self.connect("""SELECT COUNT(*) FROM FighterFights
    WHERE FighterID=? AND FightID IN (SELECT FightID FROM Fights WHERE Method='SUB');
    ""","one",fighterArray[j])
            totalDecs=self.connect("""SELECT COUNT(*) FROM FighterFights
    WHERE FighterID=? AND FightID IN (SELECT FightID FROM Fights WHERE Method='DEC');
    ""","one",fighterArray[j])
            totalKos=self.connect("""SELECT COUNT(*) FROM FighterFights
    WHERE FighterID=? AND FightID IN (SELECT FightID FROM Fights WHERE Method='KO');
    ""","one",fighterArray[j])
            fighterDecRate=(totalDecs[0]/totalFights[0])*100
            fighterSubRate=(totalSubs[0]/totalFights[0])*100
            fighterKoRate=(totalKos[0]/totalFights[0])*100
            #Find out what fighters do above average
            userData=self.connect("""SELECT SubOpinion,KoOpinion,DecisionOpinion,favouriteFighter FROM Users WHERE Username=?""","one",(self.usernameToken))
            fighterOpinionArray=[False,False,False,False]
            if fighterSubRate>averageSubRate:
                fighterOpinionArray[0]=True
            if fighterDecRate>averageDecRate:
                fighterOpinionArray[1]=True
            if fighterKoRate>averageKoRate:
                fighterOpinionArray[2]=True
            if fighterArray[j] == userData[3]:
                fighterOpinionArray[3]=True
            entertainmentRating=75
            #Apply rating for each thign they do above average
            for i in range(3):
                if fighterOpinionArray[i] == True:
                    if i != 3:
                        entertainmentRating=entertainmentRating-(6.25*(5-userData[i]))
                    else:
                        entertainmentRating=entertainmentRating+50
        entertainmentRating=entertainmentRating/2 
        #output
        self.ui.EntertainmentResult.setText("Entertainment:"+str(math.trunc(entertainmentRating))+"%")
      
    #Leaderboard subproblems
    ##Initialize leaderboard
    def initLeaderboard(self):
        headers = ["FighterID", "Name", "Rating", "Preference", "Weight Class", "Birthdate", "Gym"]
        userData = self.connect("SELECT SubOpinion, KoOpinion, DecisionOpinion, favouriteFighter FROM Users WHERE Username=?","one",(self.usernameToken,))
        if not userData:
            userData = (1, 1, 1, 0)
        self.subOpinion, self.koOpinion, self.decOpinion, favouriteFighter = userData
        totalFights = self.connect("SELECT COUNT(*) FROM Fights;", "one", None)[0]
        totalSubs = self.connect("SELECT COUNT(*) FROM Fights WHERE Method='SUB';", "one", None)[0]
        totalKos = self.connect("SELECT COUNT(*) FROM Fights WHERE Method='KO';", "one", None)[0]
        totalDecs = self.connect("SELECT COUNT(*) FROM Fights WHERE Method='DEC';", "one", None)[0]
        averageSubRate = (totalSubs / totalFights) * 100 if totalFights else 0
        averageKoRate = (totalKos / totalFights) * 100 if totalFights else 0
        averageDecRate = (totalDecs / totalFights) * 100 if totalFights else 0
        rows = self.connect("SELECT FighterID, Name, EloRating, WeightClass, Birthdate, Gym FROM Fighters;","many",None)
        if not rows:
            rows=[]
        newRows = []
        for fighterID, fighterName, eloRating, weightClass, birthdate, gym in rows:
        # get fighter stats
            fighterFightCount = self.connect(
                "SELECT COUNT(*) FROM FighterFights WHERE FighterID=?;",
                "one",
                (fighterID,)
            )[0]
            if fighterFightCount == 0:
                preferenceScore = 0
            else:
                fighterSubs = self.connect("""
                    SELECT COUNT(*) FROM FighterFights
                    WHERE FighterID=? AND FightID IN
                    (SELECT FightID FROM Fights WHERE Method='SUB');
                """, "one", (fighterID,))[0]
                fighterKos = self.connect("""
                    SELECT COUNT(*) FROM FighterFights
                    WHERE FighterID=? AND FightID IN
                    (SELECT FightID FROM Fights WHERE Method='KO');
                """, "one", (fighterID,))[0]
                fighterDecs = self.connect("""
                    SELECT COUNT(*) FROM FighterFights
                    WHERE FighterID=? AND FightID IN
                    (SELECT FightID FROM Fights WHERE Method='DEC');
                """, "one", (fighterID,))[0]
                fighterSubRate = (fighterSubs / fighterFightCount) * 100
                fighterKoRate = (fighterKos / fighterFightCount) * 100
                fighterDecRate = (fighterDecs / fighterFightCount) * 100
                preferenceScore = 0
                if fighterSubRate > averageSubRate:
                    preferenceScore += self.subOpinion * 6
                if fighterKoRate > averageKoRate:
                    preferenceScore += self.koOpinion * 6
                if fighterDecRate > averageDecRate:
                    preferenceScore += self.decOpinion * 6
                if fighterID == favouriteFighter:
                    preferenceScore += 20
                preferenceScore = round(preferenceScore)
            newRows.append((fighterID,fighterName,eloRating,preferenceScore,weightClass,birthdate,gym))
        rows = newRows
        rows=list(rows)
        #Insertion sort
        for i in range(1, len(rows)):
            currentItem = rows[i]
            j = i - 1
            while j >= 0 and (
                rows[j][2] < currentItem[2] or
                (rows[j][2] == currentItem[2] and str(rows[j][1]).lower() > str(currentItem[1]).lower())
            ):
                rows[j + 1] = rows[j]
                j -= 1
            rows[j + 1] = currentItem
        #Build the table
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(headers)
        for row in rows:
            itemRow = []
            for colIndex, field in enumerate(row):
                item = QStandardItem()
                if headers[colIndex] in ["Rating", "Preference"] and isinstance(field, (int, float)):
                    item.setData(round(field), Qt.DisplayRole)
                else:
                    item.setData(str(field), Qt.DisplayRole)
                itemRow.append(item)
            model.appendRow(itemRow)
        self.ui.leaderboardTableView.setModel(model)
        self.ui.leaderboardTableView.setColumnHidden(0, True)
        header = self.ui.leaderboardTableView.horizontalHeader()
        header.setSortIndicator(2, Qt.DescendingOrder)   
        self.ui.leaderboardTableView.setSortingEnabled(True)   
        header = self.ui.leaderboardTableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.ui.leaderboardTableView.setAlternatingRowColors(True)
        self.ui.leaderboardTableView.verticalHeader().setDefaultSectionSize(30)
        header.setDefaultAlignment(Qt.AlignCenter)
        self.ui.leaderboardFighterBelts.setText("")
        self.ui.leaderboardFighterRecord.setText("")
        if self.isAdmin == 0:
            self.ui.leaderboardManageListButton.hide()
        else:
            self.ui.leaderboardManageListButton.show()
        self.navigate(2)
    ##Load fighter data from leaderboard
    def leaderboardLoadFighterData(self,index):
        TotalLosses=0
        TotalWins=0
        TotalDraws=0
        model = self.ui.leaderboardTableView.model()
        row, col, value = self.onTableClick(self.ui.leaderboardTableView, index)
        self.leaderboardCurrentId = model.item(row,0).text()
        fighterData=self.connect("SELECT * FROM Fighters WHERE FighterID=?;","one",(self.leaderboardCurrentId,))
        self.ui.leaderboardFighterName.setText(fighterData[1])
        #Load image
        if fighterData[8]:
            print("loadimage")
            self.loadImage(fighterData[8],self.ui.leaderboardImage,None,None)
        else:
            self.loadImage(None,self.ui.leaderboardImage,"File","defaultpfp.png")
        #Load record
        fighterFightData = self.connect(
    "SELECT Result FROM FighterFights WHERE FighterID=?;",
    "many",
    (self.leaderboardCurrentId,) 
)
        for (result,) in fighterFightData:
            if result == "W":
                TotalWins += 1
            elif result == "L":
                TotalLosses += 1
            elif result == "D" or result == "NC":
                TotalDraws += 1
        record=str(TotalWins)+"-"+str(TotalDraws)+"-"+str(TotalLosses)
        self.ui.leaderboardFighterRecord.setText(record)
        #Load belts
        beltsList=self.connect("SELECT * FROM Belts WHERE FighterID=(SELECT FighterID FROM Fighters WHERE FighterID=?);","many",(self.leaderboardCurrentId,))
        if beltsList:
                beltsText="Belts: "
                edge=0
                for row in beltsList:
                    edge=edge+1
                    if edge == len(beltsList):
                        beltsText=beltsText+str(row[1])
                    else:
                        beltsText=beltsText+str(row[1])+","
                self.ui.leaderboardFighterBelts.setText(beltsText)
        else:
            self.ui.leaderboardFighterBelts.setText("")
    ##Search for fighters in the leaderboard
    def leaderboardSearchFighter(self):
        model=self.ui.leaderboardTableView.model()
        searchTerm = self.ui.leaderboardFighterSearch.toPlainText()
        #Reject blank searches
        if searchTerm == "" or searchTerm == " ":
            return
        headers = ["FighterID", "Name", "Weight Class", "Birthdate", "Gym"]
        distances = self.tableDistances(searchTerm)
        newTable = []
        #Sort ids by edit distance
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
        #Load model
        for row,rowData in enumerate(newTable):
            for col, value in enumerate(rowData):
                model.setItem(row,col,QStandardItem(value)) 
        self.ui.leaderboardTableView.setColumnHidden(0, True)
      
    #Admin-side profile subroutines
    ##Initialise fighter proifle page on admin side
    def showProfileAdmin(self,index):
        self.fighterId = index.siblingAtColumn(0).data() 
        print("display profile of fighterID "+str(self.fighterId,))
        fighterData=self.connect("SELECT * FROM Fighters WHERE FighterId=?","one",(self.fighterId,))
        print("fighterdata:"+str(fighterData))
        self.ui.modifyFighterTitle.setText("Editing Fighter:"+str(fighterData[1]))
        self.ui.modifyFighterName.setPlainText(str(fighterData[1]))
        self.ui.modifyFighterGym.setPlainText(str(fighterData[4]))
        self.ui.modifyFighterImageLink.setPlainText(str(fighterData[8]))
        #Dealing with height and reach
        height=float(fighterData[9])
        reach=float(fighterData[10])
        if height is not None and reach is not None:
            truncHeight = int(height)
            truncReach  = int(reach)
            inchesHeight = int(round((height - truncHeight) * 100))
            inchesReach = int(round((reach  - truncReach)  * 100))
            textHeight = f"{truncHeight}'{inchesHeight:02d}\""
            textReach  = f"{truncReach}'{inchesReach:02d}\""
            self.ui.modifyFighterHeight.setPlainText(textHeight)
            self.ui.modifyFighterReach.setPlainText(textReach)
        else:   
            self.ui.modifyFighterHeight.setPlainText(height)
            self.ui.modifyFighterReach.setPlainText(reach)
        #load image
        self.loadImage(fighterData[8],self.ui.modifyFighterImage,None,None)
        #deal with weight classes
        self.ui.modifyFighterWeightclass.setCurrentText(fighterData[2])
        #deal with birthday
        date = QDate.fromString(fighterData[3], "yyyy-MM-dd")
        self.ui.modifyFighterBirthday.setDate(date)
        #display fights
        query = """
        DECLARE @FighterID INT = ?;

        SELECT
            FighterFights.FighterFightsID AS [FighterFightsID],
            FighterFights.FightID         AS [FightID],

            (SELECT TOP 1 FighterFights.FighterFightsID
            FROM FighterFights
            WHERE FighterFights.FightID = Fights.FightID
            AND FighterFights.FighterID <> @FighterID
            ORDER BY FighterFights.FighterFightsID) AS [OppFFID],

            (SELECT TOP 1 FighterFights.FighterID
            FROM FighterFights
            WHERE FighterFights.FightID = Fights.FightID
            AND FighterFights.FighterID <> @FighterID
            ORDER BY FighterFights.FighterFightsID) AS [OpponentID],

            Fights.EventID,
            FighterFights.Result AS [Result],
            Fights.Method        AS [Method],
            Fights.EndRound      AS [Round],
            CAST((DATEPART(HOUR, Fights.EndTime) * 60) + DATEPART(MINUTE, Fights.EndTime) AS varchar(10))
            + ':'
            + RIGHT('0' + CAST(DATEPART(SECOND, Fights.EndTime) AS varchar(2)), 2) AS [Time],
            Fights.Title
        FROM FighterFights
        JOIN Fights ON Fights.FightID = FighterFights.FightID
        LEFT JOIN Events ON Events.EventID = Fights.EventID
        WHERE FighterFights.FighterID = @FighterID
        ORDER BY Fights.FightID DESC;
        """
        self.genTable(
            (query, "many", (self.fighterId,)),
            headers=["FighterFightsID","FightID","OppFFID","OpponentID","EventID","Result","Method","Round","Time","Title"],
            table=self.ui.modifyFighterFightsTable,
            isFightsTable=True
        )

        self.ui.modifyFighterFightsTable.setColumnHidden(0, True)  
        self.ui.modifyFighterFightsTable.setColumnHidden(1, True) 
        self.ui.modifyFighterFightsTable.setColumnHidden(2, True)  
        #display belts
        beltsList=self.connect("SELECT * FROM Belts WHERE FighterID=(SELECT FighterID FROM Fighters WHERE FighterID=?);","many",(fighterData[0],))
        if beltsList:
            beltsText="Belts: "
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
        nameToSubmit=self.ui.modifyFighterName.toPlainText()
        gymToSubmit=self.ui.modifyFighterGym.toPlainText()
        weightClassToSubmit=self.ui.modifyFighterWeightclass.currentText()
        #Validating name
        if nameToSubmit.strip() == "":
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Name is blank.")
            return
        if len(nameToSubmit) > 60:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Name is too long.")
            return
        if "\n" in nameToSubmit or "\r" in nameToSubmit:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No linebreaks allowed in names.")
            return
        #Gym validation
        if len(gymToSubmit) > 80:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Name is too long.")
            return
        if "\n" in gymToSubmit or "\r" in gymToSubmit:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "No linebreaks allowed in names.")
            return
        #validating date
        dateToSubmit=self.ui.modifyFighterBirthday.date().toString("yyyy-MM-dd")
        q = self.ui.modifyFighterBirthday.date()
        dob = date(q.year(), q.month(), q.day())
        today = date.today()
        minAge = 16
        maxAge = 60
        if dob > today:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Birthday cannot be in the feature")
            return
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < minAge or age > maxAge:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Age must be between 16 and 60")
            return
        imageLinkToSubmit=self.ui.modifyFighterImageLink.toPlainText()
        #Image validation
        if imageLinkToSubmit=="None" or imageLinkToSubmit.strip()=="":
            imageLinkToSubmit=None
        else:
            if len(imageLinkToSubmit)>256:
                QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Image link too long.")
                return
            
        #validating height and reach
        heightSubmitted=self.ui.modifyFighterHeight.toPlainText()
        reachSubmitted=self.ui.modifyFighterReach.toPlainText()
        convertedHeight=self.feetConversion(heightSubmitted)
        convertedReach=self.feetConversion(reachSubmitted)
        if convertedHeight == False or convertedReach == False:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Bad Height/Reach Value (Bad format/range)")
            return
        #Checking for duplicates
        existingFighter=self.connect("SELECT COUNT(*) FROM Fighters WHERE Name=? AND Birthdate=?","one",(nameToSubmit,dateToSubmit,))
        if existingFighter[0] > 1:
            QtWidgets.QMessageBox.critical(None, "Submit Edits Error", "Fighter already exists")
            return
        self.connect("UPDATE Fighters SET Name=?,WeightClass=?,Birthdate=?,Gym=?,ImageURL=?,Height=?,Reach=? WHERE FighterID=?","none",(nameToSubmit,weightClassToSubmit,dateToSubmit,gymToSubmit,imageLinkToSubmit,convertedHeight,convertedReach,self.fighterId)) 
    #Tooltip for fighter IDs   
    def fighterIdTooltip(self, index):
        if not index.isValid():
            QToolTip.hideText()
            return

        if index.column() != 3:
            QToolTip.hideText()
            return

        try:
            fid = int(index.data())
        except (TypeError, ValueError):
            QToolTip.hideText()
            return
        fighterNameMap = dict(self.connect("SELECT FighterID, Name FROM Fighters;", "many", None) or [])
        name = fighterNameMap.get(fid)
        if name:
            QToolTip.showText(QCursor.pos(), name, self.ui.modifyFighterFightsTable)
        else:
            QToolTip.hideText()
            QToolTip.hideText()
    ##Add fight button
    def modifyFighterAddFight(self):
        print("Add fight")
        query = """
        DECLARE @FightID INT;
        DECLARE @FighterID INT = ?;

        INSERT INTO dbo.Fights (EventID, Method, EndRound, EndTime, Title)
        VALUES (NULL, NULL, NULL, NULL, NULL);

        SET @FightID = SCOPE_IDENTITY();

        INSERT INTO dbo.FighterFights (FightID, FighterID, Corner, Result)
        VALUES (@FightID, @FighterID, NULL, NULL);
        """
        self.connect(query, "none", (self.fighterId,))
        self.refreshAdminFightsTable()
    #Delete fight
    def modifyFighterDeleteFight(self):
        print("Delete fight")

        table = self.ui.modifyFighterFightsTable
        model = table.model()
        index = table.currentIndex()

        if (model is None) or (not index.isValid()):
            QtWidgets.QMessageBox.critical(None, "Delete fight", "Select a fight first.")
            return

        row = index.row()

        # Column 1 is FightID
        fightID = model.index(row, 1).data()

        if fightID is None:
            QtWidgets.QMessageBox.critical(None, "Delete fight", "FightID is None.")
            return

        query = """
        DELETE FROM dbo.FighterFights WHERE FightID = ?;
        DELETE FROM dbo.Fights        WHERE FightID = ?;
        """
        self.connect(query, "none", (fightID, fightID))

        # refresh 
        self.refreshAdminFightsTable()
    ##Select fight 
    def modifyFighterSelectFight(self,index):
        self.modFighterCurrentId=index.siblingAtColumn(1).data() 
    
    #User-side profile subroutines
    ##Intialise fighter profile page on user side
    def showProfileUser(self,index):
        self.ui.nodatamessage.hide()
        fighterId = index.siblingAtColumn(0).data() 
        self.userProfileFighterID=fighterId
        print("display profile of fighterID "+fighterId)
        fighterData=self.connect("SELECT * FROM Fighters WHERE FighterId=?","one",(fighterId))
        print("fighterdata:"+str(fighterData))
        self.ui.fighterProfileName.setText(str(fighterData[1]))
        self.loadImage(fighterData[8],self.ui.fighterProfileImage,None,None)
        #Dealing with height and reach
        height=float(fighterData[9])
        reach=float(fighterData[10])
        if height is not None and reach is not None:
            truncHeight = int(height)
            truncReach  = int(reach)
            inchesHeight = int(round((height - truncHeight) * 10))
            inchesReach = int(round((reach  - truncReach)  * 10))
            textHeight = f"{truncHeight}'{inchesHeight}\""
            textReach  = f"{truncReach}'{inchesReach}\""
            self.ui.fighterProfileHeightLabel.setText("Height:"+str(textHeight))
            self.ui.fighterProfileReachLabel.setText("Reach:"+str(textReach))
        else:   
            self.ui.fighterProfileHeightLabel.setPlainText(height)
            self.ui.fighterProfileReachLabel.setPlainText(reach)
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
    Events.Date AS [Date],
    FighterFights.Result AS [Result],
    Fights.Method AS [Method],
    Fights.EndRound AS [Round],
    CAST((DATEPART(HOUR, Fights.EndTime) * 60) + DATEPART(MINUTE, Fights.EndTime) AS varchar(10))
    + ':'
    + RIGHT('0' + CAST(DATEPART(SECOND, Fights.EndTime) AS varchar(2)), 2) AS [Time]
FROM FighterFights
JOIN Fights ON Fights.FightID = FighterFights.FightID
JOIN Events ON Events.EventID = Fights.EventID"""
        self.genTable((query,"many",(fighterData[0],)),["Opponent Name","Event Name","Date","Result","Method","Round","Time"],self.ui.fighterProfileFights,isFightsTable=False)
        #Piechart-Figure out totals (sub/ko/dec)
        totalWinsQuery="""SELECT COUNT(*)
FROM FighterFights
JOIN Fights ON Fights.FightID = FighterFights.FightID
WHERE FighterFights.FighterID = ?
  AND FighterFights.Result = 'W'
  AND Fights.Method = ?;"""
        winsBreakdown=[self.connect(totalWinsQuery,"one",(fighterData[0],"SUB")),self.connect(totalWinsQuery,"one",(fighterData[0],"KO")),self.connect(totalWinsQuery,"one",(fighterData[0],"DEC"))]
        totalWinsQuery="""SELECT COUNT(*)
FROM FighterFights
JOIN Fights ON Fights.FightID = FighterFights.FightID
WHERE FighterFights.FighterID = ?
  AND FighterFights.Result = 'L'
  AND Fights.Method = ?;"""
        lossBreakdown=[self.connect(totalWinsQuery,"one",(fighterData[0],"SUB")),self.connect(totalWinsQuery,"one",(fighterData[0],"KO")),self.connect(totalWinsQuery,"one",(fighterData[0],"DEC"))]
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
        if len(sizes)==0 or all0==True:
            self.ui.nodatamessage.show()
        def makeAutopct(values):
            total = sum(values)
            def Autopct(pct):
                value = pct * total / 100.0
                return f"{pct:.1f}%\n({value:.0f})"
            return Autopct
        ax.pie(sizes, labels=labels, autopct=makeAutopct(sizes), colors=colourIndex)
        ax.axis("equal") 
        layout = self.ui.fighterGraph.layout()
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
        #Deal with streak 
        fightRows=self.connect(query,"many",self.userProfileFighterID)
        if fightRows is None:
            self.ui.fighterProfileStreakLabel.setText("No Streak")
        else:
            streakLoopTerminated=True
            fight=1
            streakResult=fightRows[0][3]
            if streakResult is not None:
                streak=1
                while streakLoopTerminated == True and fight<(len(fightRows)-1):
                    if fightRows[fight][3] == streakResult:
                        streak=streak+1
                        fight=fight+1
                    else:
                        streakLoopTerminated=False
                self.ui.fighterProfileStreakLabel.setText("Streak:"+str(streakResult)+"-"+str(streak))
        #deal with rating
        self.displayApproval(self.userProfileFighterID)
        #Deal with top 10 fighters they have fought against
        notableFightsQuery="""SELECT 
    Fighters.Name AS OpponentName,
    FighterFights.Result
FROM FighterFights
JOIN FighterFights AS FighterFights2 
    ON FighterFights.FightID = FighterFights2.FightID
JOIN Fighters 
    ON Fighters.FighterID = FighterFights2.FighterID
WHERE FighterFights.FighterID = ?
  AND FighterFights2.FighterID <> ?
  AND FighterFights2.FighterID IN (
        SELECT TOP 10 FighterID
        FROM Fighters
        WHERE WeightClass = (
            SELECT WeightClass FROM Fighters WHERE FighterID = ?
        )
        ORDER BY EloRating DESC
  );"""
        notableFightsList=self.connect(notableFightsQuery,"many",(self.userProfileFighterID,self.userProfileFighterID,self.userProfileFighterID,))
        notableFightsString="Notable Fights:"
        notableLimit=3
        for i in range(len(notableFightsList)):
            notableFight=""
            if notableLimit>0:
                notableFight=notableFight+notableFightsList[i][0]
                notableFight=notableFight+"("+notableFightsList[i][1]+")"+" "
                notableFightsString=notableFightsString+notableFight
            notableLimit=notableLimit-1
        self.ui.fighterProfileNotableFights.setText(notableFightsString)
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
        rating=1 if int(rating) == 1 else 0
        user=self.connect("SELECT userId FROM Users where Username=?;","one",(self.usernameToken))
        if not user:
            QtWidgets.QMessageBox.critical(None, "Error", "No user found")
            return
        userID=user[0]
        existing=self.connect("SELECT Rating FROM Approvals WHERE UserID=? AND FighterID=?","one",(userID,fighterID))
        if not existing:
            self.connect("INSERT INTO Approvals VALUES (?,?,?)","none",(userID,fighterID,rating))
        if existing:
            self.connect("UPDATE Approvals SET Rating=? WHERE UserID=? AND FighterID=?","none",(rating,userID,self.userProfileFighterID))
        self.displayApproval(fighterID)
        
    #Options subroutines
    ##Initialize options
    def initOptions(self):
        self.genTable(("SELECT * FROM Belts","many",None),["Belt ID","Name","Holder ID"],self.ui.beltsTable,"Belts","BeltID",["BeltID","WeightClass","FighterID"])
        self.genTable(("SELECT * FROM Events","many",None),["Event ID","Name","Location","Date"],self.ui.eventsTable,"Events","EventID",["EventID","Name","Location","Date"])
        self.pendingEdits.clear()
        self.navigate(8)
    #Belt clicked
    def beltClicked(self,index):
        self.beltClickedIndex=index.siblingAtColumn(0).data() 
    ##Add belt
    def addBelt(self):
        self.connect("INSERT INTO Belts VALUES (?,1)","none",("Blank Belt",))
        self.genTable(("SELECT * FROM Belts","many",None),["Belt ID","Title","Holder ID"],self.ui.beltsTable)
        self.submitEdits(self.ui.beltsTable)
        print("Add belt")
    ##Delete belt
    def deleteBelt(self):
        print("Delete belt")
        if self.beltClickedIndex is not None:
            self.connect("DELETE FROM Belts WHERE BeltID=?","none",(self.beltClickedIndex,))
            self.connect("""UPDATE Fights SET WeightClass='RETIRED' WHERE WeightClass=(SELECT WeightClass FROM Belts WHERE BeltID=?)""","none",(self.beltClickedIndex,))
            self.genTable(("SELECT * FROM Belts","many",None),["Belt ID","Title","Holder ID"],self.ui.beltsTable)
            self.submitEdits()
    #Event clicked
    def eventClicked(self,index):
        self.eventClickedIndex=index.siblingAtColumn(0).data() 
    ##Add event
    def addEvent(self):
        self.connect("INSERT INTO Events (Name,Location,Date) VALUES (?,?,?)","none",("name","location","1984-02-02"))
        self.genTable(("SELECT * FROM Events","many",None),["Event ID","Name","Location","Date"],self.ui.eventsTable) 
        self.submitEdits(self.ui.eventsTable)       
        print("Add event")
    ##Delete event
    def deleteEvent(self):
        print("Delete event")
        if self.eventClickedIndex is not None:
            dependencies=False
            #Check for dependencies and erase them if so ask if they want them gone as well
            depedencyQuery=self.connect("SELECT COUNT(*) FROM Fights WHERE EventID=?;","one",(self.eventClickedIndex,))
            dependencyCount=depedencyQuery[0]
            dependencies=(dependencyCount>0)
            if dependencies==True:
                reply = QMessageBox.question(
                    self,                        
                    "Confirm Action",             
                    "This event has multiple dependencies. You will have to delete them as well. Proceed?", 
                    QMessageBox.Yes | QMessageBox.No,        
                    QMessageBox.No               
                )
                if reply == QMessageBox.Yes:
                    #Erase event and its dependencies
                    self.connect("DELETE FROM FighterFights WHERE FightID IN (SELECT FightID FROM Fights WHERE EventID=?);","none",(self.eventClickedIndex))
                    self.connect("DELETE FROM Fights WHERE EventID=?;","none",(self.eventClickedIndex))
                else:
                    return
            if dependencies==False: 
                self.connect("DELETE FROM Events WHERE EventID=?","none",(self.eventClickedIndex,))
            self.genTable(("SELECT * FROM Events","many",None),["Event ID","Name","Location","Date"],self.ui.eventsTable)  
            self.submitEdits(self.ui.eventsTable)
            
    ##Auto-assign belts
    def autoAssignBelts(self):
        print("auto assign belts")
        #Find distinct weight classes with no belt
        beltLessDivisions=self.connect("""SELECT DISTINCT WeightClass
FROM Belts 
WHERE FighterID IS NULL;""","many",None)
        if beltLessDivisions is None or len(beltLessDivisions)==0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("No beltless divisions found.")
            msg.setWindowTitle("Auto Assignment Successful")
            msg.exec()
            return
        for belt in range(len(beltLessDivisions)):
            #Find the last winner of the title fight in the beltless division
            mostRecentWinner=self.connect("""SELECT FighterID FROM FighterFights
WHERE Result='W' AND FightID=(SELECT TOP 1 FightID 
FROM Fights
INNER JOIN Events ON Events.EventID=Fights.EventID
WHERE Title = ?);""","one",(beltLessDivisions[belt][0],))
            if mostRecentWinner is None:
                continue 
            #Assign belt to last winner
            self.connect("""UPDATE Belts
SET FighterID=?
WHERE WeightClass=?""","none",(mostRecentWinner[0],beltLessDivisions[belt][0],))
            self.genTable(("SELECT * FROM Belts","many",None),["Belt ID","Name","Holder ID"],self.ui.beltsTable,"Belts","BeltID",["BeltID","WeightClass","FighterID"])
        msg = QMessageBox()
        msg.setText("Belt Auto-Assignment Complete."+str(len(beltLessDivisions))+" beltless divisons found.")
        msg.setWindowTitle("Auto-Assignment Complete")
        msg.setIcon(QMessageBox.Information)
        msg.exec()
            
    ##Import from UFC
    def importFromUFC(self):
        print("Import from UFC")
    ##Refresh admin  fights table
    def refreshAdminFightsTable(self):
        query = """
        DECLARE @FighterID INT = ?;

        SELECT
            FighterFights.FighterFightsID AS [FighterFightsID],
            FighterFights.FightID         AS [FightID],

            (SELECT TOP 1 FighterFights.FighterFightsID
            FROM FighterFights
            WHERE FighterFights.FightID = Fights.FightID
            AND FighterFights.FighterID <> @FighterID
            ORDER BY FighterFights.FighterFightsID) AS [OppFFID],

            (SELECT TOP 1 FighterFights.FighterID
            FROM FighterFights
            WHERE FighterFights.FightID = Fights.FightID
            AND FighterFights.FighterID <> @FighterID
            ORDER BY FighterFights.FighterFightsID) AS [OpponentID],

            Fights.EventID,
            FighterFights.Result AS [Result],
            Fights.Method        AS [Method],
            Fights.EndRound      AS [Round],
            CONVERT(char(8), Fights.EndTime, 108) AS [Time],
            Fights.Title
        FROM FighterFights
        JOIN Fights ON Fights.FightID = FighterFights.FightID
        LEFT JOIN Events ON Events.EventID = Fights.EventID
        WHERE FighterFights.FighterID = @FighterID
        ORDER BY Fights.FightID DESC;
        """
        #Generate admin fights table
        self.genTable(
            (query, "many", (self.fighterId,)),
            headers=["FighterFightsID","FightID","OppFFID","OpponentID","EventID","Result","Method","Round","Time","Title"],
            table=self.ui.modifyFighterFightsTable,
            isFightsTable=True
        )

        # hide internal IDs only
        self.ui.modifyFighterFightsTable.setColumnHidden(0, True)
        self.ui.modifyFighterFightsTable.setColumnHidden(1, True)
        self.ui.modifyFighterFightsTable.setColumnHidden(2, True)

        # make sure OpponentID and EventID are visible
        self.ui.modifyFighterFightsTable.setColumnHidden(3, False)
        self.ui.modifyFighterFightsTable.setColumnHidden(4, False)
    #run elo calculations    
    def updateEloRatings(self):
        #firstly, set all ratings to defaults
        self.connect("""UPDATE dbo.Fighters
SET
    EloRating = 1500,
    Volatility = 0.06,
    RatingDeviation = 200;""","none",None)
        #then bring up the fights table
        query="""
WITH ff AS (
    SELECT
        FighterFights.FightID,
        FighterFights.FighterID,
        FighterFights.Result,
        ROW_NUMBER() OVER (
            PARTITION BY FighterFights.FightID
            ORDER BY FighterFights.FighterFightsID
        ) AS rn
    FROM dbo.FighterFights
),
paired AS (
    SELECT
        ff.FightID,
        MAX(CASE WHEN ff.rn = 1 THEN Fighters.FighterID  END) AS FighterA,
        MAX(CASE WHEN ff.rn = 2 THEN Fighters.FighterID  END) AS FighterB,
        MAX(CASE WHEN ff.rn = 1 THEN ff.Result      END) AS FighterAResult,
        MAX(CASE WHEN ff.rn = 2 THEN ff.Result      END) AS FighterBResult
    FROM ff
    JOIN dbo.Fighters
        ON Fighters.FighterID = ff.FighterID
    GROUP BY ff.FightID
)
SELECT

    paired.FighterA      AS FighterA,
    paired.FighterB      AS FighterB,
    paired.FighterAResult AS Result
FROM paired
LEFT JOIN dbo.Fights
    ON Fights.FightID = paired.FightID
LEFT JOIN dbo.Events
    ON Events.EventID = Fights.EventID
ORDER BY
    CASE WHEN Events.[Date] IS NULL THEN 1 ELSE 0 END,
    Events.[Date] ASC,
    paired.FightID ASC;
"""
        chronoLogFightsTable=self.connect(query,"many",None)
        #then systematically update all the elo ratings
        for fight in range(len(chronoLogFightsTable)):
            fighterA=chronoLogFightsTable[fight][0]
            fighterB=chronoLogFightsTable[fight][1]
            resultText=chronoLogFightsTable[fight][2]
            if resultText=="W":
                result=1
            elif resultText=="L":
                result=0
            else:
                result=0.5
            fighterAdata=self.connect("SELECT * FROM Fighters WHERE FighterID=?","one",(fighterA,))
            fighterBdata=self.connect("SELECT * FROM Fighters WHERE FighterID=?","one",(fighterB,))
            r1=fighterAdata[5]
            r2=fighterBdata[5]
            rd1=fighterAdata[7]
            rd2=fighterBdata[7]
            sigma1=fighterAdata[6]
            sigma2=fighterBdata[6]
            newR1, newRd1, newSigma1, newR2, newRd2, newSigma2=glicko2(r1, rd1, sigma1, r2, rd2, sigma2, result)
            sql = """
            UPDATE dbo.Fighters
            SET EloRating = ?, RatingDeviation = ?, Volatility = ?
            WHERE FighterID = ?;

            UPDATE dbo.Fighters
            SET EloRating = ?, RatingDeviation = ?, Volatility = ?
            WHERE FighterID = ?;
            """
            params = (
                newR1, newRd1, newSigma1, fighterA,
                newR2, newRd2, newSigma2, fighterB
            )
            self.connect(sql, "none", params)
            #Round them all
            self.connect("""UPDATE dbo.Fighters SET EloRating = ROUND(EloRating, 0);""", "none", None)
            #finally, refresh fighter table
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Elo Calculations Successful")
        msg.setWindowTitle("ELO Calculations Complete")
        msg.exec()
        self.loadModifyFighter()
    
    ##Validation subroutines
    #Feet validation and conversion
    def feetConversion(self,length):
        try:
            #Format validation
            inputLength = length.strip().replace('"', '')
            splitLength = inputLength.split("'")
            if len(splitLength)!=2:
                return(False)
            feet=splitLength[0]
            if int(feet) > 8 or int(feet) < 3:
                return(False)
            inches=splitLength[1]
            if int(inches) > 11 or int(inches) < 0:
                return(False)
            #Range validation
            if feet<4 or feet>8:
                return False
            #Conversion for storage
            inches=float(inches)/100
            length=float(inches)+float(feet)
            return(length)
        except:
            return(False)
   
#Glicko elo calculation
#I'm dealing with a really complex algorithm here so to stay truthful to the algorithm, I had to make it so the variables had names that can be quite hard to identify. Here is the dictionary for all of the variables i use:
#r1 and r1 are player ratings for 1 and 2 respectively
#rd1 and rd2 are rating deviation
#sigma1 and sigma2 is volatility
#result is the match outcome from the perspective of P1
#Tau is the volatility constraint which limits how volatility can change in one update
#Eps is tolerance which stops root search when the bracket is small enough
#s1 and s2 converts results into a numeric score
#scale is the scale constant which puts rating and rating deviation into internal units
#pi2 is just pi squared and its used in the phi formula
#toMu toPhi and toR are internal conversions
#g is the impact function which decreases the impact of opponents who don't have high certainty
#E is the expected score function 
#updateSingle performs the glicko update
#s is player score in the match
#mu is the internal rating of p1
#phi is the internal rating deviation of p1
#muJ is the internal rating of the opponent
#phiJ is the rd of the opponent
#gJ is the opponents weight i.e. how heavily the opponent affects the update
#eJ is the expected score given internal values
#v is the variance which measures how important the fight is and how much rating can move
#delta is the improvement signal which measures the difference between real performance and expectations
#a is the log variance for sigma squared which is the starting point for the volatility update
#f(x) is the root function which gives the new volatility from its root 
#x represents the ln of the root squared during root finding
#ex converts back from log space
#num and den are the numerator piece and the denominator piece of the glicko 2 volatility equation
#A and B are the bracket endpoints
#K is the step count between brackets
#fa and fb are the function result at the end points
#C is the candidate for x from interpolation (linear)
#fC is the function result at the point of the candidate
#sigmaPrime is the new volatility
#phiStar is the deviation with volatility before applying the match info
#phiPrime is the updated deviation
#muPrime is the updated internal rating
def glicko2(r1, rd1, sigma1, r2, rd2, sigma2, result,
                      tau=0.5, eps=1e-6):
        #Turn result into a score 1 being p1 win 0.5 being a draw and 0.0 being a loss for p1
        if isinstance(result, (int, float)):
            s1 = float(result)  # expect 1 0.5 or 0
        else:
            res = str(result).strip().lower()
            if res in ("win", "w", "red"):     
                s1 = 1.0
            elif res in ("loss", "l", "blue"):
                s1 = 0.0
            elif res in ("draw", "d"):
                s1 = 0.5
            else:
                raise ValueError("result must be Win/Loss/Draw or 1/0/0.5")
        #Handle opponent result (same principles here i'm just doing the opposite of whatever p1 got)
        s2 = 1.0 - s1 if s1 != 0.5 else 0.5 
        #convert to glicko algorithm scales
        SCALE = 173.7178
        PI2 = math.pi ** 2

        def toMu(r):  return (r - 1500.0) / SCALE
        def toPhi(rd): return rd / SCALE
        def toR(mu):  return mu * SCALE + 1500.0
        def toRd(phi): return phi * SCALE
        #Find impact score algorithm
        def g(phi):
            return 1.0 / math.sqrt(1.0 + (3.0 * phi * phi) / PI2)
        #Find expected score algorithm
        def E(mu, muJ, phiJ):
            return 1.0 / (1.0 + math.exp(-g(phiJ) * (mu - muJ)))
        #1v1 update
        def update_single(r, rd, sigma, rOp, rdOp, s):
            #Convert to glicko 2 internal scale
            mu = toMu(r)
            phi = toPhi(rd)
            muJ = toMu(rOp)
            phiJ = toPhi(rdOp)
            #Figure out expected score
            gJ = g(phiJ)
            eJ = E(mu, muJ, phiJ)
            #Calculate variance
            v = 1.0 / (gJ * gJ * eJ * (1.0 - eJ))
            #Calculate estimated improvement
            delta = v * gJ * (s - eJ)
            #Log volatility term used in updating volatility
            a = math.log(sigma * sigma)
            #This function has to be solved in order to get the updated volatility
            def f(x):
                ex = math.exp(x)
                #Glicko 2 volatility update equation
                num = ex * (delta * delta - phi * phi - v - ex)
                den = 2.0 * (phi * phi + v + ex) * (phi * phi + v + ex)
                return (num / den) - ((x - a) / (tau * tau))
            # find A,B for root finding using bracketing so that fa and fb are different signs
            A = a
            if delta * delta > (phi * phi + v):
                B = math.log(delta * delta - phi * phi - v)
            else:
                #step left until sign changes
                k = 1
                B = a - k * tau
                while f(B) < 0:
                    k += 1
                    B = a - k * tau
            fA = f(A)
            fB = f(B)

            # Illinois algorithm (better algorithm for solving for x)
            while abs(B - A) > eps:
                #interpolate root
                C = A + (A - B) * fA / (fB - fA)
                fC = f(C)
                #keep part that brackets root
                if fC * fB < 0:
                    A, fA = B, fB
                else:
                    #the illinois algorithm dampens one side in order to avoid stagnation
                    fA = fA / 2.0
                B, fB = C, fC
            #Figure out sigma prime
            sigmaPrime = math.exp(A / 2.0)
            #Pre rating deviation with volatility uncertainty
            phiStar = math.sqrt(phi * phi + sigmaPrime * sigmaPrime)
            #New deviation with variance included
            phiPrime = 1.0 / math.sqrt((1.0 / (phiStar * phiStar)) + (1.0 / v))
            #New rating calculated
            muPrime = mu + (phiPrime * phiPrime) * gJ * (s - eJ)
            #Convert rating values back to ordinary scale
            return toR(muPrime), toRd(phiPrime), sigmaPrime
        #Update both players 
        newR1, newRd1, newSigma1 = update_single(r1, rd1, sigma1, r2, rd2, s1)
        newR2, newRd2, newSigma2 = update_single(r2, rd2, sigma2, r1, rd1, s2)
        #Return values
        return newR1, newRd1, newSigma1, newR2, newRd2, newSigma2

#Threading signals init for image threading
class ImageSignals(QObject):
    finished = pyqtSignal(bytes, object)
    error = pyqtSignal(str, object)
#Worker init for image threading
class ImageWorker(QRunnable):
    def __init__(self, url, element):
        super().__init__()
        self.url = url
        self.element = element
        self.signals = ImageSignals()
    @pyqtSlot()
    def run(self):
        try:
            headers = {"User-Agent": "TJ CompSci tomjubb29@gmail.com"}
            response = requests.get(self.url, headers=headers, timeout=5)   
            if "image" in response.headers.get("Content-Type", ""):
                self.signals.finished.emit(response.content, self.element)
            else:
                self.signals.error.emit(f"Not an image: {self.url}", self.element)
        except requests.RequestException as e:
            self.signals.error.emit(str(e), self.element)
 
 
#Show the Window
print("Show the Window")
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    iconPath = os.path.join(os.path.dirname(__file__), "..", "Assets", "icon.ico")
    app.setWindowIcon(QIcon(iconPath)) 
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
