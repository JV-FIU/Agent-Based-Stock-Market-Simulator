#RMSC03-based accuracy program for Agent-based Stock Market Simulator
#Created by: Jorge Valdes-Santiago
#Date created:  July 16, 2023
#Updated:       July 20, 2023

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
from widgets.ImageViewer import ImageWidget as ImgWidget

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
        self.ui.setWindowTitle("Agent-Based Stock Market Simulator - Simulate Future")

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
        
        #Check if both times are in the past
        #FIXME: This simulator version is supposed to run only with past dates, not future ones
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
                
                print("Simulation complete")

                self.graphLiquidity()
            else:
                print("End time not in the future relative to Start time")
        else:
            print("Start and End times must be in the past")
        
            

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
        self.generateImage((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_Midprice.png"), self.ui.imageContainer_1)
        self.generateImage((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_Spread.png"), self.ui.imageContainer_2)
        self.generateImage((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_R.png"), self.ui.imageContainer_3)
        self.generateImage((str(epoch_time) + "_" + stockSym + "_LiquidityGraph_TV.png"), self.ui.imageContainer_4)

            
        #Clean up
        sys.argv.clear()
        sys.argv.append(TemporaryStorage)
        os.chdir('../../')
        #print("Current Directory: ", os.getcwd())
        print("Graphing process completed!")
         
    def generateImage(self, imageLocation, displayName):
        
        #Delete Text
        displayName.setText("")

        #Display image 
        displayName.setPixmap(QPixmap(imageLocation).scaled(displayName.width(), displayName.height(), QtCore.Qt.KeepAspectRatio))
