#ABIDES Agent-based Stock Market Simulator main file
#Created by: Jorge Valdes-Santiago
#Date created: June 26, 2023
#Modified: July 21, 2023

from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6 import QtCore

#Configuration files
from widgets.Predictor import RMSC03Predictor
from widgets.Tester import RMSC03Tester



class AbidesMain(QtCore.QObject):
    def __init__(self):
        super().__init__()

        #Get main program UI
        global mainWindow
        mainWindow = loader.load("absms_main.ui", None) #Load UI
        self.mainWindow = mainWindow

        #Configuration options
        self.predictor = RMSC03Predictor()
        self.tester = RMSC03Tester()
        

        #Select configuration file
        def selectConfiguration():
            selection = mainWindow.configBox.currentText()
            #print(selection)

            #Launch selected simulator configuration file
            if selection == 'Simulate Future Date':
                print("Opening Future sim...")
                self.predictor.show()
            elif selection == 'Test Simulation Result Accuracy':
                print("Opening Past sim...")
                self.tester.show()
            else:
                print("Please select an option")

        #Launch main window
        self.mainWindow.launchButton.clicked.connect(selectConfiguration)
        self.mainWindow.show()


#Main program
if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    loader = QUiLoader()
    main = AbidesMain()
    app.exec()
