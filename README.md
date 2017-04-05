
# YAST - Yet Another Sessionization Tool

YAST is a simple sessionization tool that can be used to generate sessions from a log file. Currently, YAST supports Apache Common log, Apache Combined log and Squid Proxy log format. The generated sessions can be saved in CSV format which can be used for Data Mining applications.

![YAST Screenshot](https://s28.postimg.org/f3ai2gjzh/Screenshot_from_2017-04-05_18-47-52.png)
# Features
* Supports Apache Common/Combined and Squid Common log format
* Supports Windows and Linux (Ubuntu 16.04)
* User defined session time
* User friendly GUI
* Save result of each step in CSV format

# Requirements -
* Python 3.x
* Pip
* PyQt4
* SqlAlchemy
* Sqlite3

# Installation
1. Clone or download the repository. Clone using ```git clone https://github.com/jarifibrahim/YAST```

2. Download and Install Python 3.x. Installation instructions can be found [here](https://www.python.org/downloads/).
3. Install PyQt4.

	On Ubuntu ```sudo apt-get install python-qt4```. 
	
    Read [this](http://pyqt.sourceforge.net/Docs/PyQt4/installation.html) for installing PyQt4 on windows.

4. Install remaining dependencies using ```pip install -r requirements.txt```

# Usage
The entire process is divided into 3 steps
1. Tokeinization - Spliting the log file into individual tokens
2. Filtering - Removing unnecessary entries from the log file
3. Sessionization - Actual sessionization of the input.


Run ``` python src/yast_gui.py```.
Choose an input log file, file format and start Tokenization. Once the tokenization is completed the result can be saved in CSV format. You can specify file formats to be removed during filtering of the log file. Sessionization can be performed after tokenization is completed.
