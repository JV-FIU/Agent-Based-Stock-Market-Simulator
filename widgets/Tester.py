#RMSC03-based accuracy program for Agent-based Stock Market Simulator
#Created by: Jorge Valdes-Santiago
#Date created:  July 16, 2023
#Updated:       July 23, 2023

#IMPORTANT NOTE: All code related to finding content in directories are using the location of absms.py as reference

from PySide6 import QtCore
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
import argparse
import sys
import importlib
import time
import json
import os

import pandas as pd

loader = QUiLoader()

class RMSC03Tester(QtCore.QObject): #An object wrapping around the ui
    #Global variables
    epoch_time = 0
    stockSym = "NDAQ" #Default stock symbol for now
    alreadyRun = False
    alreadyGraphed = False

    def __init__(self):
        super().__init__()
        #Load window
        self.ui = loader.load("widgets/UI/RMSC03_Past.ui", None)
        self.ui.setWindowTitle("Agent-Based Stock Market Simulator - Compare Simulation data")

        #Set time to local time zone
        self.ui.startTime.setTimeSpec(QtCore.Qt.TimeSpec.LocalTime)
        self.ui.endTime.setTimeSpec(QtCore.Qt.TimeSpec.LocalTime)

        #Set default values
        self.ui.startTime.setDate(
            QtCore.QDate.currentDate())
        self.ui.startTime.setTime(
            QtCore.QTime(9, 30, 0))
        self.ui.endTime.setDate(
            QtCore.QDate.currentDate())
        self.ui.endTime.setTime(
            QtCore.QTime(16, 0, 0))
        self.ui.simDate.setDate(
            QtCore.QDate.currentDate())
        global stockSym
        self.ui.stockSymbol.setText("NDAQ")

        #Set up display images
        self.setUpImage(self.ui.imageContainer_1, "widgets/UI/Image2.jpeg")
        self.setUpImage(self.ui.realData, "widgets/UI/Image3.jpeg")

        #Set default values to global variables
        global alreadyRun
        alreadyRun = False

        global alreadyGraphed
        alreadyGraphed = False

        #Connect methods to events
        self.ui.pushButton.clicked.connect(self.simulate)
        self.ui.fetchData.clicked.connect(self.fetchData)



    def show(self):#Display window
        self.ui.show() 

    def simulate(self): #Start simulation
        #Declare variables
        global epoch_time
        global stockSym
        global alreadyRun

        epoch_time = int(time.time())
        stockSym = self.ui.stockSymbol.text()
        startTime = self.ui.startTime
        endTime = self.ui.endTime
        selectedDate = self.ui.simDate

        #Store time values (bug fix)
        start = self.ui.startTime.time()
        end = self.ui.endTime.time()

        #Set dates (bug fix)
        startTime.setDate(
            QtCore.QDate(selectedDate.date()))
        startTime.setTime(start)

        endTime.setDate(
            QtCore.QDate(selectedDate.date()))
        endTime.setTime(end)

        
        #Check if both times are in the past
        if (startTime.dateTime().toSecsSinceEpoch() < epoch_time) and (endTime.dateTime().toSecsSinceEpoch() < epoch_time):
            
            #Check if end time is in the future, relative to the start time
            if (startTime.dateTime().toSecsSinceEpoch() < endTime.dateTime().toSecsSinceEpoch()): 
                print("Stock symbol:    ", stockSym)
                print("Selected Date:   ", selectedDate.date().toString("yyyy / MM / dd"))
                print("Start Time:      ", startTime.time().toString("hh:mm:ss"))
                print("End Time:        ", endTime.time().toString("hh:mm:ss"))
                #os.chdir('../')

                #Set up seed
                seed = 0
                if (self.ui.checkBox.isChecked()):
                    seed = self.ui.seedSelector.value()
                else:
                    seed = int(pd.Timestamp.now().timestamp() * 1000000) % (2 ** 32 - 1) #Generate random seed (Temporary) 

                print("Seed: ", seed)

                #ABIDES functionality
                parser = argparse.ArgumentParser(description='Simulation configuration.')
                parser.add_argument('-c', '--config', required=True,
                                    help='Name of config file to execute')
                parser.add_argument('--config-help', action='store_true',
                                    help='Print argument options for the specific config file.')
                #Add arguments since most of the scripts are CMD-based
                #print("Length of sys.argv is ", len(sys.argv))
                sys.argv.append("-c")
                sys.argv.append("rmsc03")
                sys.argv.append("-t")
                sys.argv.append(self.ui.stockSymbol.text())
                sys.argv.append("-d")
                sys.argv.append(selectedDate.date().toString('yyyyMMdd'))
                sys.argv.append("-s")
                sys.argv.append(str(seed))
                sys.argv.append("-l")
                sys.argv.append((str(epoch_time) + "_" + str(self.ui.stockSymbol.text())))   
                sys.argv.append("--start-time")
                sys.argv.append(startTime.time().toString("hh:mm:ss"))
                sys.argv.append("--end-time")
                sys.argv.append(endTime.time().toString("hh:mm:ss"))
                #print("New length of sys.argv is ", len(sys.argv))
                args, config_args = parser.parse_known_args() 
                config_file = args.config
                #Default start time is 9:30:00
                #Default end time is  11:30:00

                # First parameter supplied is config file.
                print("Config file: ", config_file)  
                #for i in sys.argv:
                #    print("Argument:  ", i)
                print("Running Simulation... This might take a while")
                #config = importlib.import_module('config.{}'.format(config_file), package=None)
                
                if alreadyRun == False:
                    importlib.import_module('config.{}'.format(config_file), package=None)
                    alreadyRun = True
                else:
                    importlib.reload(importlib.import_module('config.{}'.format(config_file), package=None))
                    
                
                #Clear arguments after running simulation
                TemporaryStorage = sys.argv[0]
                sys.argv.clear()
                sys.argv.append(TemporaryStorage)

                #Open json file used for plotting and edit variables
                with open('util/plotting/configs/plot_configuration.json', 'r+') as jsonFile:
                    timeData = json.load(jsonFile)                              #Load json file
                    timeData['xmin'] = startTime.time().toString("hh:mm:ss")    #Set start time
                    timeData['xmax'] = endTime.time().toString("hh:mm:ss")      #Set simulation end time
                    jsonFile.seek(0)                                            #Go to top of file
                    json.dump(timeData, jsonFile, indent=4)                     #Insert edits into file
                    jsonFile.truncate()                                         #Delete whatever characters are left
                    jsonFile.close()      
                
                #Open json file to store latest simulation configuration 
                with open('util/plotting/configs/latest_simulation.json', 'r+') as simFile:
                    simData = json.load(simFile)                              #Load json file
                    
                    #Save latest simulation time data
                    simData['year'] = selectedDate.date().year()              #Set year
                    simData['month'] = selectedDate.date().month()            #Set month
                    simData['day'] = selectedDate.date().day()                #Set day
                    
                    #Set start time
                    simData['start-hour'] = startTime.time().hour()           #Set start hour
                    simData['start-minute'] = startTime.time().minute()       #Set start minutes

                    #Set end time
                    simData['end-hour'] = endTime.time().hour()               #Set end hour
                    simData['end-minute'] = endTime.time().minute()           #Set end minutes 

                    #Set data name
                    simData['dataName'] = (str(epoch_time) + "_" + str(self.ui.stockSymbol.text()))

                    #Set ticker
                    simData['ticker'] = stockSym
                
                    simFile.seek(0)                                            #Go to top of file
                    json.dump(simData, simFile, indent=4)                      #Insert edits into file
                    simFile.truncate()                                         #Delete whatever characters are left
                    simFile.close()

                print("Simulation complete")

                #Graph data
                self.graphLiquidity(selectedDate.date().toString('yyyyMMdd'),
                                    startTime.time().toString("hh:mm:ss"),
                                    endTime.time().toString("hh:mm:ss"))
            else:
                print("End time not in the future relative to Start time")
        else:
            print("Start and End times must be in the past")
        
            

    def graphLiquidity(self, date, startTime, endTime, data=None, tickerSym=None): #Graph data
        global epoch_time
        global stockSym
        global alreadyGraphed

        #print("New Epoch time is: ", epoch_time)
        TemporaryStorage = sys.argv[0]
        sys.argv.clear()
        sys.argv.append('liquidity_telemetry.py')

        #print("Current dir " + os.getcwd())
        #Change directory
        os.chdir('.\\util\\plotting')
        parser = argparse.ArgumentParser(description='CLI utility for inspecting liquidity issues and transacted volumes')

        #print("New Directory: ", os.getcwd())

        if (data or tickerSym) is None: #NOTE: Must keep an eye on this if statement
            #Insert arguments
            sys.argv.append("../../log/" + (str(epoch_time) + "_" + stockSym) + "/EXCHANGE_AGENT.bz2")  
            sys.argv.append("../../log/" + (str(epoch_time) + "_" + stockSym) + "/ORDERBOOK_" + stockSym + "_FULL.bz2") 
            sys.argv.append("-o")
            sys.argv.append(str(epoch_time) + "_" + stockSym + "_LiquidityGraph")         
            sys.argv.append("-c")
            sys.argv.append("configs/plot_configuration.json")
            sys.argv.append("-s")
            sys.argv.append(stockSym)
            sys.argv.append("-d")
            sys.argv.append(date)
            sys.argv.append("-st")
            sys.argv.append(startTime)
            sys.argv.append("-et")
            sys.argv.append(endTime)                       

                                
            args, config_args = parser.parse_known_args() 
            #config_file = args.config

            #Check if graphing program has been executed, else reload program
            if alreadyGraphed == False:
                importlib.import_module('util.plotting.{}'.format('LT_Market_Comparison'), package=None)
                alreadyGraphed = True
            else:
                importlib.reload(importlib.import_module('util.plotting.{}'.format('LT_Market_Comparison'), package=None))
            
            #Generate graphs
            self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_Midprice.png"), self.ui.imageContainer_1)
            self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_Spread.png"), self.ui.imageContainer_2)
            self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_R.png"), self.ui.imageContainer_3)
            self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_TV.png"), self.ui.imageContainer_4)        
            self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_CrossCorrelation.png"), self.ui.crossCorrelation)
            self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_OpeningPrices.png"), self.ui.realData)
        else:
            #Insert arguments
            sys.argv.append("../../log/" + data + "/EXCHANGE_AGENT.bz2")  
            sys.argv.append("../../log/" + data + "/ORDERBOOK_" + tickerSym + "_FULL.bz2") 
            sys.argv.append("-o")
            sys.argv.append(data + "_LiquidityGraph")         
            sys.argv.append("-c")
            sys.argv.append("configs/plot_configuration.json")
            sys.argv.append("-s")
            sys.argv.append(tickerSym)
            sys.argv.append("-d")
            sys.argv.append(date)
            sys.argv.append("-st")
            sys.argv.append(startTime)
            sys.argv.append("-et")
            sys.argv.append(endTime)                       

                                
            args, config_args = parser.parse_known_args() 
            #config_file = args.config

            #Check if graphing program has been executed, else reload program
            if alreadyGraphed == False:
                importlib.import_module('util.plotting.{}'.format('LT_Market_Comparison'), package=None)
                alreadyGraphed = True
            else:
                importlib.reload(importlib.import_module('util.plotting.{}'.format('LT_Market_Comparison'), package=None))
            
            #Generate graphs
            self.generateImage2((data + "_LiquidityGraph_Midprice.png"), self.ui.imageContainer_1)
            self.generateImage2((data + "_LiquidityGraph_Spread.png"), self.ui.imageContainer_2)
            self.generateImage2((data + "_LiquidityGraph_R.png"), self.ui.imageContainer_3)
            self.generateImage2((data + "_LiquidityGraph_TV.png"), self.ui.imageContainer_4)
            self.generateImage2((data + "_LiquidityGraph_CrossCorrelation.png"), self.ui.crossCorrelation)
            self.generateImage2((data + "_LiquidityGraph_OpeningPrices.png"), self.ui.realData)
            
        #Get Root Mean Square Error
        with open('configs/RMSE.json', 'r') as rmseFile:
            storedRMSE = json.load(rmseFile)                   #Load json file
            #rmse = storedRMSE['rmse']                         #Get Root Mean Square Error
            roundedRmse = storedRMSE['rounded-rmse']           #Get Rounded Root Mean Square error
            self.ui.RMSError.setText(str(roundedRmse))         #Display RMSE result
            rmseFile.close()                                   #Close file

        #Clean up
        sys.argv.clear()
        sys.argv.append(TemporaryStorage)
        os.chdir('../../')
        #print("Current Directory: ", os.getcwd())
        print("Graphing process completed!")
         


    #This method is fine, but for some reason the images of the hidden tabs are being displayed in a very low resolution
    def generateImage(self, imageLocation, displayName): 
        
        #Delete Text
        displayName.setText("")

        #Display image 
        displayName.setPixmap(QPixmap(imageLocation).scaled(displayName.width(), displayName.height(), QtCore.Qt.KeepAspectRatio))
        #print("Display width:", str(displayName.width()), "; Display height:", str(displayName.height()))

    #Temporary fix until the sizing bug is patched
    def generateImage2(self, imageLocation, displayName):
        
        #Delete Text
        displayName.setText("")

        #Temporary size fix
        w = self.ui.imageContainer_1.width()
        h = self.ui.imageContainer_1.height()

        #Display image 
        displayName.setPixmap(QPixmap(imageLocation).scaled(w, h, QtCore.Qt.KeepAspectRatio))
        #print("Display width:", str(displayName.width()), "; Display height:", str(displayName.height()))
    
    #NOTE: Might add an if statement that checks if its simulation was done within 30 from today
    #NOTE: Might also add an if statement that checks if a simulation run was done
    #if (startTime.dateTime().toSecsSinceEpoch() < epoch_time) and (endTime.dateTime().toSecsSinceEpoch() < epoch_time):
    def fetchData(self):
        print("Fetching latest simulation data...")
        epoch_time = int(time.time())
        
        #Get latest simulation configuration and set variables
        with open('util/plotting/configs/latest_simulation.json', 'r') as simFile:
            simData = json.load(simFile)    #Load json file

            #Retrieve  latest simulation configuration data
            #Get Date
            year = simData['year']
            month = simData['month']
            day = simData['day']
            
            #Get times
            startHour = simData['start-hour']
            startMinute = simData['start-minute']
            endHour = simData['end-hour']
            endMinute = simData['end-minute']

            #Get data name
            dataName = simData['dataName']

            #Get Ticker
            ticker = simData['ticker']

            #Set variables
            self.ui.startTime.setDate(
               QtCore.QDate(year, month, day))          #Set simulation date to start time
            self.ui.startTime.setTime(
               QtCore.QTime(startHour, startMinute, 0)) #Set sim start time
            self.ui.endTime.setDate(
               QtCore.QDate(year, month, day))          #Set simulation date to end time
            self.ui.endTime.setTime(
               QtCore.QTime(endHour, endMinute, 0))     #Set simulation end time
            self.ui.simDate.setDate(
               QtCore.QDate(year, month, day))          #Set simulation date
            
            self.ui.stockSymbol.setText(ticker)         #Set ticker
            
            simFile.close()

            
            #Check if the configuration times of the last simulation are in the past
            if (self.ui.startTime.dateTime().toSecsSinceEpoch() < epoch_time) and (self.ui.endTime.dateTime().toSecsSinceEpoch() < epoch_time):
                #Graph data
                self.graphLiquidity(self.ui.simDate.date().toString('yyyyMMdd'),
                                    self.ui.startTime.time().toString("hh:mm:ss"),
                                    self.ui.endTime.time().toString("hh:mm:ss"),
                                    dataName,
                                    ticker)
            else:
                print("No real life stock data is available yet, please try again later.")

    #Set defaul image on startup
    def setUpImage(self, display, imageLocation):
        #Temporary size fix
        w = self.ui.imageContainer_1.width()
        h = self.ui.imageContainer_1.height()
        display.setPixmap(QPixmap(imageLocation).scaled(w, h, QtCore.Qt.KeepAspectRatio))
            
