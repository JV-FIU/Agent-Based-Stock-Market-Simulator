#ABIDES Agent-based Stock Market Simulator main file
#Created by: Jorge Valdes-Santiago
#Date created: June 26, 2023

from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6 import QtCore

#Configuration files
from widgets.rmsc03Widget import RMSC03



class AbidesMain(QtCore.QObject):
    def __init__(self):
        super().__init__()

        #Get main program UI
        global mainWindow
        mainWindow = loader.load("MainUI.ui", None) #Load UI
        self.mainWindow = mainWindow

        #Configuration file UIs
        self.rmsc03 = RMSC03()
        

        #Select configuration file
        def selectConfigFile():
            selection = mainWindow.configBox.currentText()
            #print(selection)

            #Launch selected simulator configuration file
            if selection == 'RMSC03':
                print("Opening RMSC03...")
                self.rmsc03.show()
            else:
                print("Please select a configuration file")

        #Launch main window
        self.mainWindow.launchButton.clicked.connect(selectConfigFile)
        self.mainWindow.show()


#Main program
if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    loader = QUiLoader()
    main = AbidesMain()
    app.exec()
