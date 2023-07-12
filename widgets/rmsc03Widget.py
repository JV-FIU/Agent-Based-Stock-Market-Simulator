#RMSC03 Widget for Agent-based Stock Market Simulator
#Created by: Jorge Valdes-Santiago
#Date created: June 26, 2023

#IMPORTANT NOTE: All code related to finding content in directories are using the location of MainX.py as reference

from PySide6 import QtCore
from PySide6.QtUiTools import QUiLoader
import argparse
import sys
import importlib
import time
import os
from widgets.ImageViewer import ImageWidget as ImgWidget

loader = QUiLoader()

class RMSC03(QtCore.QObject): #An object wrapping around the ui
    #Global variables
    epoch_time = 0
    isGraphAvailable = False
    stockSym = "MSFT" #Default stock symbol for now

    def __init__(self):
        super().__init__()
        self.ui = loader.load("widgets/UI/RMSC03UI.ui", None)
        self.ui.setWindowTitle("Agent-Based Stock Market Simulator RMSC03 UI Widget Experiment - Jorge V.")
        self.ui.pushButton.clicked.connect(self.simulate)
        self.ui.graphResults.clicked.connect(self.graphLiquidity) #FIXME: Uncomment after recording video
        global isGraphAvailable
        isGraphAvailable = False

    def show(self):#Display window
        self.ui.show() 

    def simulate(self): #Start simulation
        #Declare variables
        global isGraphAvailable
        global epoch_time
        global stockSym

        epoch_time = int(time.time())
        stockSym = self.ui.stockSymbol.text()
        startTime = self.ui.startTime
        endTime = self.ui.endTime
        selectedDate = self.ui.simDate
        #print(epoch_time)

        #Check if end time is in the future, relative to the start time
        if (startTime.dateTime().toSecsSinceEpoch() < endTime.dateTime().toSecsSinceEpoch()): 
            print("Stock symbol:    ", stockSym)
            print("Selected Date:   ", selectedDate.date().toString("yyyy / MM / dd"))
            print("Start Time:      ", startTime.time().toString("hh:mm:ss"))
            print("End Time:        ", endTime.time().toString("hh:mm:ss"))
            #os.chdir('../')

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
            sys.argv.append("12")
            sys.argv.append("-l")
            sys.argv.append(str(epoch_time))   
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
            print("Running Simulation... This may take a while")
            config = importlib.import_module('config.{}'.format(config_file), package=None) #FIXME: Uncomment after debugging graph
            
            #Clear arguments after running simulation
            TemporaryStorage = sys.argv[0]
            sys.argv.clear()
            sys.argv.append(TemporaryStorage)
            
            isGraphAvailable = True
            print("Simulation complete")
        else:
            print("End time not in the future relative to Start time")

    def graphLiquidity(self):
        global epoch_time
        global stockSym

        if (isGraphAvailable): #Check if there's a graph
            print("New Epoch time is: ", epoch_time)
            TemporaryStorage = sys.argv[0]
            sys.argv.clear()
            sys.argv.append('liquidity_telemetry.py')

            print("Current dir " + os.getcwd())
            #Change directory
            os.chdir('.\\util\\plotting')
            parser = argparse.ArgumentParser(description='CLI utility for inspecting liquidity issues and transacted volumes')

            #Insert arguments
            sys.argv.append("../../log/" + str(epoch_time) + "/EXCHANGE_AGENT.bz2")  
            sys.argv.append("../../log/" + str(epoch_time) + "/ORDERBOOK_" + stockSym + "_FULL.bz2") 
            sys.argv.append("-o")
            sys.argv.append(str(epoch_time) + "_LiquidityGraph.png")         
            sys.argv.append("-c")
            sys.argv.append("configs/plot_09.30_11.30.json")    #Temporary, a json configuration file creator will be added
                            
            args, config_args = parser.parse_known_args() 
            #config_file = args.config

            config = importlib.import_module('util.plotting.{}'.format('liquidity_telemetry'), package=None)
            image = ImgWidget(str(epoch_time) + "_LiquidityGraph.png")
            image.show()
            sys.argv[0] = TemporaryStorage
            #os.chdir('../../')
            print("Current Directory: ", os.getcwd())
            print("Done")
        else:
            print("Run simulation first") 
