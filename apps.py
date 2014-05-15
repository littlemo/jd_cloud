# -*- coding: utf-8 -*-

__author__ = 'Moore.Huang'

import time
import httplib
import json
import sys
from PyQt4 import QtGui, QtCore
from apps_ui import Ui_JDSmartCloud_Apps

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class SmartCloudApps(QtGui.QWidget):
    def __init__(self,
                 product_id='41',
                 address=('apismart.jd.com', 443),
                 jd_key='iKvyNBTcB9eTDB1oqgBuxFtVI9iJB1jgBcVqHZXNGCpN19Hp',
                 parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_JDSmartCloud_Apps()
        self.ui.setupUi(self)
        self.ui.pbCheckStatus.clicked.connect(self.__is_alive)
        self.ui.pbClearLog.clicked.connect(self.__clear_log)
        self.ui.pbControlDev.clicked.connect(self.__control_dev_slot)
        self.ui.pbReadData.clicked.connect(self.__read_data_slot)
        self.ui.leFeedID.textChanged.connect(self.__update_feed_id_slot)
        self.ui.leAccessKey.textChanged.connect(self.__update_access_key_slot)

        self.access_key = self.ui.leAccessKey.text()
        self.feed_id = self.ui.leFeedID.text()

        self.product_id = product_id
        self.address = address
        self.jd_key = jd_key

        self.conn = None
        self.alive_status = None
        self.switch_status = None

        self.active_https()

    def active_https(self):
        host, port = self.address
        self.conn = httplib.HTTPSConnection(host, port)

    def __get_alive_status(self):
        host, port = self.address
        address = '%s:%s' % (host, port)

        method = 'GET'
        url = '/v1/device/%s/status' % self.feed_id
        headers_req = {'Host': address, 'JD-Key': self.access_key}

        self.conn.request(method, url, headers=headers_req)
        _res = self.conn.getresponse()

        print _res.version, _res.status, _res.reason
        if _res.status is not 200:
            print 'Err: HTTPS response.status [%s]' % _res.status
            self.conn.close()
            return False

        body_rsp = _res.read()
        body_json_rsp = json.loads(body_rsp)
        print 'len => [%d],\t data => %s' % (len(body_rsp), body_rsp)
        self.ui.pteLog.appendPlainText(body_rsp)

        try:
            key = 'code'
            if int(body_json_rsp[key]) == 200:
                self.alive_status = int(body_json_rsp['data']['status'])
            elif int(body_json_rsp[key]) == 3001:
                self.alive_status = 0
            else:
                print "body_json_rsp[%s] %d is not '200'" % (key, int(body_json_rsp[key]))
                self.conn.close()
                return False
        except KeyError:
            print 'Can not find the key[%s]!' % key
            self.conn.close()
            return False

        return True

    def close_https(self):
        if self.conn is not None:
            self.conn.close()
        else:
            print 'the conn is None!'

    def __is_alive(self):
        self.__get_alive_status()
        self.ui.pteLog.appendPlainText('刷新完成:\t%d' % self.alive_status)
        if self.alive_status == 1:
            self.ui.lStatusDisp.setPixmap(QtGui.QPixmap(_fromUtf8(":/ui/resources/green_light.png")))
            self.ui.pbControlDev.setEnabled(True)
            self.ui.pbReadData.setEnabled(True)
            return True
        elif self.alive_status == 0:
            self.ui.lStatusDisp.setPixmap(QtGui.QPixmap(_fromUtf8(":/ui/resources/red_light.png")))
            self.ui.pbControlDev.setEnabled(False)
            self.ui.pbReadData.setEnabled(False)
            return False

    def __read_data_slot(self):
        res = self.get_current_dev_all_stream()
        self.ui.pteLog.appendPlainText('读取数据:\t%s' % str(res))

    def get_current_dev_all_stream(self):
        host, port = self.address
        address = '%s:%s' % (host, port)

        method = 'GET'
        url = '/v1/feeds/%s/streams' % self.feed_id
        headers_req = {'Host': address, 'JD-Key': self.access_key}

        self.conn.request(method, url, headers=headers_req)
        _res = self.conn.getresponse()

        print _res.version, _res.status, _res.reason
        if _res.status is not 200:
            print 'Err: HTTPS response.status [%s]' % _res.status
            self.conn.close()
            return False

        # headers_rsp = _res.getheaders()
        # print headers_rsp
        body_rsp = _res.read()
        body_json_rsp = json.loads(body_rsp)
        body_json_rsp_str = json.dumps(body_json_rsp, indent=4)
        print 'len => [%d],\t data => \r\n%s' % (len(body_rsp), body_json_rsp_str)
        self.ui.pteLog.appendPlainText(body_json_rsp_str)

        try:
            key = 'code'
            if int(body_json_rsp[key]) == 200:
                for item in body_json_rsp['data']:
                    if item['stream_id'] == 'switch':
                        self.switch_status = item['current_value']
                    elif item['stream_id'] == 'temp':
                        self.ui.leTempDisp.setText(str(item['current_value']))
                print self.switch_status
                if self.switch_status == 1:
                    s = 'on'
                    self.ui.pbControlDev.setChecked(True)
                else:
                    s = 'off'
                    self.ui.pbControlDev.setChecked(False)
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/ui/resources/switch_%s.png" % s)),
                               QtGui.QIcon.Normal, QtGui.QIcon.Off)
                self.ui.pbControlDev.setIcon(icon)
            else:
                print "body_json_rsp[%s] %d is not '200'" % (key, int(body_json_rsp[key]))
                self.conn.close()
                return False
        except KeyError:
            print 'Can not find the key[%s]!' % key
            self.conn.close()
            return False

        return True

    def __control_dev_slot(self, status):
        if status is True:
            res = self.control_dev(1)
        else:
            res = self.control_dev(0)

        if self.switch_status == 1:
            s = 'on'
            self.ui.pbControlDev.setChecked(True)
        else:
            s = 'off'
            self.ui.pbControlDev.setChecked(False)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/ui/resources/switch_%s.png" % s)),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.pbControlDev.setIcon(icon)
        self.ui.pteLog.appendPlainText('设备控制:\t' + str(res))

    def control_dev(self, switch=1):
        host, port = self.address
        address = '%s:%s' % (host, port)
        time_format = '%Y-%m-%dT%H:%M:%S+0800'
        time_str = time.strftime(time_format, time.localtime())

        method = 'PUT'
        url = '/v1/feeds/%s' % self.feed_id
        headers_req = {'Host': address, 'JD-Key': self.access_key}
        body_req = [
            {
                'stream_id': 'switch',
                'current_value': str(switch),
                'at': time_str
            }
        ]
        body_json_req = json.dumps(body_req)
        print 'body => %s' % body_json_req

        self.conn.request(method, url, headers=headers_req, body=body_json_req)
        _res = self.conn.getresponse()

        print _res.version, _res.status, _res.reason
        if _res.status != 200:
            print 'Err: HTTPS response.status [%s]' % _res.status
            self.conn.close()
            return False

        body_rsp = _res.read()
        body_json_rsp = json.loads(body_rsp)
        print 'len => [%d],\t data => %s' % (len(body_rsp), body_rsp)
        self.ui.pteLog.appendPlainText(body_rsp)

        try:
            key = 'code'
            if int(body_json_rsp[key]) == 200:
                self.switch_status = int(body_json_rsp['data']['switch'])
            else:
                print "body_json_rsp[%s] %d is not '200'" % (key, int(body_json_rsp[key]))
                self.conn.close()
                return False
        except KeyError:
            print 'Can not find the key[%s]!' % key
            self.conn.close()
            return False

        return True

    def __clear_log(self):
        self.ui.pteLog.clear()

    def __update_feed_id_slot(self):
        self.feed_id = str(self.ui.leFeedID.text())

    def __update_access_key_slot(self):
        self.access_key = str(self.ui.leAccessKey.text())

app = QtGui.QApplication(sys.argv)
sca = SmartCloudApps()
sca.show()
sys.exit(app.exec_())
