import os,psutil
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTime, QTimer
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog, QMessageBox
import GUI
import sys
import json,requests,time
import subprocess
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import GraphicsLayoutWidget
import datetime


# With  uncommenting below code and adding sending in correct position
# email notification is possible with miner failure
"""import smtplib
def sendmail(maddr,mpwd): 
    server = smtplib.SMTP('smtp.live.com', 587)
    server.starttls()
    server.login(maddr, mpwd)
     
    msg = "Rig stopped working!"
    server.sendmail(maddr, maddr, msg)
    server.quit()"""

fnames=os.listdir()
name="miner --server zec-eu1.nanopool.org --user t1dA2nN87SxyL4WYh1rWBaCWNqBiwNkpRGs.1 --pass z --port 6666 --cuda_devices 0 1 --fee 0 --api --pec"
path="D:/Program Files/MultiMiner/Zec Miner/0.3.4b/"
names=[]
if 'conf.txt' in fnames:
    ops=open("conf.txt",'r').read().split('\n')
    path=ops[0]
    if 'win' in sys.platform:
        name=ops[1]
    else:
        name=ops[2]
else:
    os.chdir('/')
    drive=os.getcwd().replace('\\','/')
    for dirname, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if "miner.exe" == filename:
                names.append(dirname)
    if len(names)>0:
        d=names[0]
        d='/'.join(d.split('\\')[1:len(d.split('\\'))]) 
        path=drive+d

url='http://127.0.0.1:42000/getstat'
pricelist=["https://min-api.cryptocompare.com/data/price?fsym=ZEC&tsyms=EUR,USD,BTC,ETH",
          "https://min-api.cryptocompare.com/data/price?fsym=BTCZ&tsyms=EUR,USD,BTC,ETH"]
pops=["EUR","USD","BTC","ETH"]
nworks=["ZEC","BTCZ"]
dataurl=["https://api.zcha.in/v2/mainnet/network",
         "https://www.viciousminer.com/api/stats"]

global j,sp,dt,P,T,curve, p1, p2,p3
sp=[]
dt=[]
P=[]
T=[]

t = QTime()
t.start()
process=QtCore.QProcess()

def is_int(num):
    try:
        int(num)
        return True
    except ValueError:
        return False

class ival():
    global tval
    def __init__(self):
        self.tval=30
        self.url='http://127.0.0.1:42000/getstat'
    def new(self,num):
        self.tval=num
    def get(self):
        return self.tval
setter=ival()

class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S') for value in values]    

class Main(QtWidgets.QMainWindow, GUI.Ui_MainWindow):
    global ival
    def __init__(self, parent=None):
        self.average=[]
        self.j=90
        super(Main, self).__init__(parent)
        self.setupUi(self)
        self.SMon.clicked.connect(self.start)
        self.SelFil.clicked.connect(self.Selfile)
        self.SMine.clicked.connect(self.mine)
        self.STMine.clicked.connect(self.stmine)
        self.urladd.setText(url)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatestatus)
        self.timer.start(2000)
        self.mon = None
        self.tnow=-1
        self.path.setText(path)
        self.exeline.setText(name)
        self._want_to_close = True
        for s in pops:
            self.CASH.addItem(s)
        for s in nworks:
            self.NWORKS.addItem(s)
        self.CASH.currentIndexChanged.connect(self.seturl)
        self.NWORKS.currentIndexChanged.connect(self.seturl)
    def seturl(self):
        try:
            if self.NWORKS.currentText()=='ZEC':
                priceurl=pricelist[0]
            else:
                priceurl=pricelist[1]
            dprice = requests.get(priceurl).json()
            self.price.setText(str(dprice[self.CASH.currentText()]))
        except requests.exceptions.RequestException as e:
            self.j=0
        except TypeError:
            self.j=0
        except:
            self.j=0
        try:
            if self.NWORKS.currentText()=='ZEC':
                dnet = requests.get(dataurl[0]).json()
                self.Ndiff.setText(str(int(dnet['difficulty'])))
                self.Nhashrate.setText(str(dnet['hashrate']/1000000))
            else:
                dnet = requests.get(dataurl[1]).json()
                self.Ndiff.setText(str(int(float(dnet['pools']['bitcoinz']['poolStats']['networkDiff']))))
                self.Nhashrate.setText(str(float(int(dnet['pools']['bitcoinz']['poolStats']['networkSols'])/1000000)))
        except requests.exceptions.RequestException as e:
            self.j=0
        except:
            self.j=0
            
    def updatestatus(self):
        self.j+=1
        try:
            url=str(self.urladd.text())
            setter.url=url
            data = requests.get(url).json()
            self.GPUs.clear()
            acs=0
            rcs=0
            ts=0
            EFF=''
            for i in range(0,len(data['result'])):
                if data['result'][i]['gpu_status']==2 or data['result'][i]['gpu_status']==1:
                    status='ONLINE'
                else:
                    status='OFFLINE'
                if status=="OFFLINE" and self.Astart.isChecked()==True:
                    self.stmine()
                    self.mine()
                ts+=data['result'][i]['speed_sps']
                try:
                    EFF='{:4.2f}'.format(data['result'][i]['speed_sps']/data['result'][i]['gpu_power_usage'])+' Sol/W'
                except ZeroDivisionError:
                    EFF='0 Sol/W'
                item = "GPU "+str(data['result'][i]['cudaid'])+": "+data['result'][i]['name']+' '+status+'\tEFF: '+EFF
                acs+=data['result'][i]['accepted_shares']
                rcs+=data['result'][i]['rejected_shares']
                self.GPUs.addItem(item)
            if status=='ONLINE':
                    self.average.append(ts)
            if len(self.average)>0 and self.j>=90:
                self.AVG.setText(str(int(sum(self.average)/len(self.average))))
            self.Acs.setText('Accepted shares: '+str(acs))
            self.Rcs.setText('Rejected shares: '+str(rcs))  
            self.srv.setText(str(data['current_server']))
            self.Tspeed.setText(str(ts)+" Sol/s")
            if is_int(self.Muint.text())==False:
                self.Muint.setText("30")
            else:
                setter.new(int(self.Muint.text()))

            if self.tnow!=-1:
                thours=(time.time()-self.tnow)/3600
                try:
                    self.ASH.setText('{:.2f}'.format(acs/thours))
                except:
                    self.ASH.setText('{:.2f}'.format(0))
            
        except requests.exceptions.RequestException as e:
            item = "Not Connected"
            self.srv.setText("Not connected")
            self.GPUs.clear()
            self.GPUs.addItem(item)
            self.Tspeed.setText(" 0 Sol/s")
            self.stmine()
            if is_int(self.Muint.text())==False:
                self.Muint.setText("30")
            else:
                setter.new(int(self.Muint.text()))
            if self.Astart.isChecked()==True:
                self.mine()

        if self.j>=90:
            self.j=0
            try:
                if self.NWORKS.currentText()=='ZEC':
                    priceurl=pricelist[0]
                else:
                    priceurl=pricelist[1]
                dprice = requests.get(priceurl).json()
                self.price.setText(str(dprice[self.CASH.currentText()]))
            except requests.exceptions.RequestException as e:
                self.j=0
            except TypeError:
                self.j=0
            except:
                self.j=0
            try:
                if self.NWORKS.currentText()=='ZEC':
                    dnet = requests.get(dataurl[0]).json()
                    self.Ndiff.setText(str(int(dnet['difficulty'])))
                    self.Nhashrate.setText(str(dnet['hashrate']/1000000))
                else:
                    dnet = requests.get(dataurl[1]).json()
                    self.Ndiff.setText(str(int(float(dnet['pools']['bitcoinz']['poolStats']['networkDiff']))))
                    self.Nhashrate.setText(str(float(int(dnet['pools']['bitcoinz']['poolStats']['networkSols'])/1000000)))
            except requests.exceptions.RequestException as e:
                self.j=0
            except TypeError:
                self.j=0
            except:
                self.j=0
        

    def mine(self):
        d=self.path.text()
        name=self.exeline.text()
        if d!='Path to the file used to start miner' and d!='':
            if os.path.isfile(d)==True:
                d='/'.join(d.split('/')[:-1])
            try:
                os.chdir(d)
                process.start(name)
                self.tnow=time.time()
            except PermissionError:
                QMessageBox.critical(self,"Error","Problems when accessing directory",QMessageBox.Ok)
            except FileNotFoundError:
                QMessageBox.critical(self,"Error","Bad directory path",QMessageBox.Ok)
    def stmine(self):
        process.kill()
        #kill_proc_tree(os.getpid())

    def Selfile(self):
        fpath=''
        fpath=self.openFileNameDialog()
        self.path.setText(fpath)

    def openFileNameDialog(self):    
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            return str(fileName)
        else:
            return 'Path to the file used to start miner'
   
    def start(self):
        if self.mon is None:
            self.mon=Second()
        self.mon.show()

    def closeEvent(self, event):
        if self._want_to_close:
            try:
                self.mon.close()
            except:
                i=0
            try:
                process.kill()
            except:
                i=0
            super(Main, self).closeEvent(event) 
class Second(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):

        super(Second, self).__init__(parent)
        self.T=[]
        self.P=[]
        self.sp=[]
        self.dt=[]
        self.eff=[]
        url=setter.url

        try:
            url=setter.url
            l= requests.get(url).json()
            for i in range(0,len(l['result'])):
                self.T.append([])
                self.P.append([])
                self.sp.append([])
                self.eff.append([])
        except requests.exceptions.RequestException as e:
                i=0
            
        self.resize(1000,800)
        self.setWindowTitle('Performance monitor')
        pg.setConfigOptions(antialias=True)
        
        self.p1 = self.addPlot(title="GPUs speed", axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.curve = []
        #self.p1.addLegend()
        vb = self.addViewBox()#
        vb.setMaximumWidth(100)
        legend = pg.LegendItem()
        legend.setParentItem(vb)
        legend.anchor((0,0), (0,0))#
        
        self.nextRow()
        self.p2= self.addPlot(title="Temperature", axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        #self.p2.addLegend()
        self.curve1=[]
        self.nextRow()
        self.p3= self.addPlot(title="Power", axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        #self.p3.addLegend()
        self.curve2=[]
        self.nextRow()
        self.p4= self.addPlot(title="Effiency", axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        #self.p4.addLegend()
        self.curve3=[]
        colors=[[255,0,0],[0,255,0],[0,0,255],[0,255,255],[255,0,255],[255,255,0],[125,125,0],[125,0,125],[0,125,125],[255,150,50],[255,50,150]]
        for i in range(0,len(self.T)):
            self.curve.append(self.p1.plot(pen='y',symbolBrush=(colors[i][0],colors[i][1],colors[i][2]), symbolPen='w',name='n GPU '+str(i)))                    
            self.curve1.append(self.p2.plot(pen='y',symbolBrush=(colors[i][0],colors[i][1],colors[i][2]), symbolPen='w',name='GPU '+str(i)))
            self.curve2.append(self.p3.plot(pen='y',symbolBrush=(colors[i][0],colors[i][1],colors[i][2]), symbolPen='w',name='GPU '+str(i)))
            self.curve3.append(self.p4.plot(pen='y',symbolBrush=(colors[i][0],colors[i][1],colors[i][2]), symbolPen='w',name='GPU '+str(i)))
            legend.addItem(self.curve[i],name=self.curve[i].name())        
        self.update()

    def update(self):
        try:
            url=setter.url
            l= requests.get(url).json()
            ts=0
            if len(self.T)<len(l['result']):
                self.__init__()
            for i in range(0,len(l['result'])):
                
                self.T[i].append(l['result'][i]['temperature'])
                self.P[i].append(l['result'][i]['gpu_power_usage'])
                self.sp[i].append(l['result'][i]['speed_sps'])
                try:
                    self.eff[i].append(l['result'][i]['speed_sps']/l['result'][i]['gpu_power_usage'])
                except ZeroDivisionError:
                    self.eff[i].append(0)
            self.dt.append(time.time())
            for i in range(0,len(self.T)):
                self.curve[i].setData(x=self.dt,y=self.sp[i])                
                self.curve1[i].setData(x=self.dt,y=self.T[i])
                self.curve2[i].setData(x=self.dt,y=self.P[i])
                self.curve3[i].setData(x=self.dt,y=self.eff[i])
            self.p1.enableAutoRange('xy', True)
            self.p2.enableAutoRange('xy', True)
            self.p3.enableAutoRange('xy', True)
            self.p4.enableAutoRange('xy', True)
            self.timer2 = QtCore.QTimer()
            self.timer2.timeout.connect(self.update)
            self.timer2.setInterval(setter.tval*1000)
            self.timer2.start()
        except requests.exceptions.RequestException as e:
            self.timer2 = QtCore.QTimer()
            self.timer2.timeout.connect(self.update)
            self.timer2.setInterval(setter.tval*1000)
            self.timer2.start()
        
        
def kill_proc_tree(pid, including_parent=False):    
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    gone, still_alive = psutil.wait_procs(children, timeout=5)
        
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    form = Main()
    form.show()
    app.exec_()

main()
