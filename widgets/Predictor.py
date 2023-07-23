#RMSC03-based predicting program for Agent-based Stock Market Simulator
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

class RMSC03Predictor(QtCore.QObject): #An object wrapping around the ui
    #Global variables
    epoch_time = 0
    stockSym = "NDAQ" #Default stock symbol for now
    alreadyRun = False
    alreadyGraphed = False

    def __init__(self):
        super().__init__()
        #Load window
        self.ui = loader.load("widgets/UI/RMSC03_Future.ui", None)
        self.ui.setWindowTitle("Agent-Based Stock Market Simulator - Simulate Future")

        
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

        #Place picture
        self.setUpImage(self.ui.imageContainer_1, "widgets/UI/Image2.jpeg")

        #Connect methods to events
        self.ui.pushButton.clicked.connect(self.simulate)
        
        #Set default values to global variables
        global alreadyRun
        alreadyRun = False

        global alreadyGraphed
        alreadyGraphed = False


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
        

        #Check if any of both times is in the future
        if ((startTime.dateTime().toSecsSinceEpoch() > epoch_time) or (endTime.dateTime().toSecsSinceEpoch() > epoch_time)):
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
                dataName = (str(epoch_time) + "_" + str(self.ui.stockSymbol.text()))

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
                sys.argv.append(dataName)   
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
                    simData['dataName'] = (str(epoch_time) + "_" + stockSym)

                    #Set ticker
                    simData['ticker'] = stockSym

                    #QUESTION: Would it be a good idea to store the seed used for the simulation?

                    simFile.seek(0)                                            #Go to top of file
                    json.dump(simData, simFile, indent=4)                      #Insert edits into file
                    simFile.truncate()                                         #Delete whatever characters are left
                    simFile.close()

                print("Simulation complete")

                self.graphLiquidity() 
            else:
                print("End time not in the future relative to Start time")
        else:
            print("Start or End time not in future")
            
            ''' #Uncomment to debug time-related problems
            print("Epoch (Now): ", epoch_time)
            print("Start Epoch: ", startTime.dateTime().toSecsSinceEpoch())
            print("End Epoch:   ", endTime.dateTime().toSecsSinceEpoch())
            print("Today: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time)))
            print("Start time:  ", startTime.dateTime().toLocalTime().toString('yyyy / MM / dd  hh:mm t'))
            print("End time:    ", endTime.dateTime().toLocalTime().toString('yyyy / MM / dd  hh:mm t'))
            print(str(startTime.timeSpec()))
            if (startTime.dateTime().toSecsSinceEpoch() > epoch_time):
                print("Start time not in future")
            elif (endTime.dateTime().toSecsSinceEpoch() > epoch_time):
                print("End time not in future")
            else:
                print("Both times not in future")
            '''

        
            

    def graphLiquidity(self): #Graph data
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

        #Insert arguments
        sys.argv.append("../../log/" + (str(epoch_time) + "_" + stockSym) + "/EXCHANGE_AGENT.bz2")  
        sys.argv.append("../../log/" + (str(epoch_time) + "_" + stockSym) + "/ORDERBOOK_" + stockSym + "_FULL.bz2") 
        sys.argv.append("-o")
        sys.argv.append(str(epoch_time) + "_" + stockSym + "_LiquidityGraph")         
        sys.argv.append("-c")
        sys.argv.append("configs/plot_configuration.json")  
                            
        args, config_args = parser.parse_known_args() 
        #config_file = args.config

        #Check if graphing program has been executed, else reload program
        if alreadyGraphed == False:
            importlib.import_module('util.plotting.{}'.format('liquidity_telemetry_multi'), package=None)
            alreadyGraphed = True
        else:
            importlib.reload(importlib.import_module('util.plotting.{}'.format('liquidity_telemetry_multi'), package=None))
        
        #Generate graphs
        self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_Midprice.png"), self.ui.imageContainer_1)
        self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_Spread.png"), self.ui.imageContainer_2)
        self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_R.png"), self.ui.imageContainer_3)
        self.generateImage2((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_TV.png"), self.ui.imageContainer_4)

            
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
        print("Display width:", str(displayName.width()), "; Display height:", str(displayName.height()))

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

    #Set defaul image at startup
    def setUpImage(self, display, imageLocation):
        #Temporary size fix
        w = self.ui.imageContainer_1.width()
        h = self.ui.imageContainer_1.height()
        display.setPixmap(QPixmap(imageLocation).scaled(w, h, QtCore.Qt.KeepAspectRatio))
            
