# -*- coding: utf-8 -*-

__author__ = 'Moore.Huang'

import httplib
import json
import sys
from PyQt4 import QtGui, QtCore
from src.apps.apps_ui import Ui_JDSmartCloud_Apps
from src.http_server import HTTPServer

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class SmartCloudApps(QtGui.QWidget):
    def __init__(self,
                 address=('apismart.jd.com', httplib.HTTPS_PORT),
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

        self.host, self.port = address
        self.jd_key = jd_key

        self.access_key = self.ui.leAccessKey.text()
        self.feed_id = self.ui.leFeedID.text()

        self.alive_status = None
        self.switch_status = None

        self.http_server = HTTPServer(address)

    def __get_alive_status(self):
        url = '/v1/device/%s/status' % self.feed_id
        headers_req = {'Host': self.host, 'JD-Key': self.access_key}

        rc = self.http_server.run_https_req('GET', url, headers_req)
        if rc is False:
            return False

        _res = self.http_server.get_response()
        if _res is None:
            self.ui.pteLog.appendPlainText(u'获取响应包错误！')
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
                self.http_server.disconnect_https()
                return False
            else:
                print "body_json_rsp[%s] %d is not '200'" % (key, int(body_json_rsp[key]))
                self.__update_alive_pixmap()
                self.http_server.disconnect_https()
                return False
        except KeyError:
            print 'Can not find the key[%s]!' % key
            self.http_server.disconnect_https()
            return False

        self.http_server.disconnect_https()
        return True

    def __update_alive_pixmap(self):
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
        else:
            print 'Err: alive_status is %d' % self.alive_status
            return False

    def __is_alive(self):
        self.__get_alive_status()
        self.ui.pteLog.appendPlainText(u'刷新完成:\t%d' % self.alive_status)
        return self.__update_alive_pixmap()

    def __read_data_slot(self):
        res = self.get_current_dev_all_stream()
        self.ui.pteLog.appendPlainText(u'读取数据:\t%s' % str(res))

    def get_current_dev_all_stream(self):
        url = '/v1/feeds/%s/streams' % self.feed_id
        headers_req = {'Host': self.host, 'JD-Key': self.access_key}

        rc = self.http_server.run_https_req('GET', url, headers_req)
        if rc is False:
            return False

        _res = self.http_server.get_response()
        if _res is None:
            self.ui.pteLog.appendPlainText(u'获取响应包错误！')
            return False

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
                self.__update_control_dev()
            else:
                print "body_json_rsp[%s] %d is not '200'" % (key, int(body_json_rsp[key]))
                self.http_server.disconnect_https()
                return False
        except KeyError:
            print 'Can not find the key[%s]!' % key
            self.http_server.disconnect_https()
            return False

        self.http_server.disconnect_https()
        return True

    def __update_control_dev(self):
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

    def __control_dev_slot(self, status):
        res = self.control_dev(int(status))
        self.__update_control_dev()
        self.ui.pteLog.appendPlainText(u'设备控制:\t' + str(res))

    def control_dev(self, switch=1):
        time_str = self.http_server.get_time_str()

        url = '/v1/feeds/%s' % self.feed_id
        headers_req = {'Host': self.host, 'JD-Key': self.access_key}
        body_req = [
            {
                'stream_id': 'switch',
                'current_value': str(switch),
                'at': time_str
            }
        ]
        body_req_str = json.dumps(body_req)
        print 'body => %s' % body_req_str

        rc = self.http_server.run_https_req('PUT', url, headers_req, body_req)
        if rc is False:
            return False

        _res = self.http_server.get_response()
        if _res is None:
            self.ui.pteLog.appendPlainText(u'获取响应包错误！')
            return False

        body_rsp = _res.read()
        body_json_rsp = json.loads(body_rsp)
        print 'len => [%d],\t data => %s' % (len(body_rsp), body_rsp)
        self.ui.pteLog.appendPlainText(body_rsp)

        try:
            key = 'code'
            if int(body_json_rsp[key]) == 200:
                self.switch_status = int(body_json_rsp['data']['switch'])
            elif int(body_json_rsp[key]) == 2004:
                self.__is_alive()
                return False
            else:
                print "body_json_rsp[%s] %d is not '200'" % (key, int(body_json_rsp[key]))
                self.http_server.disconnect_https()
                return False
        except KeyError:
            print 'Can not find the key[%s]!' % key
            self.http_server.disconnect_https()
            return False

        self.http_server.disconnect_https()
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