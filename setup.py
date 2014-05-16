# -*- coding: utf-8 -*-

__author__ = 'Moore.Huang'


from distutils.core import setup
import py2exe

# "dll_excludes": ["MSVCP90.dll"]
includes = ["encodings", "encodings.*", 'sip']
options = {"py2exe": {"compressed": 1, "optimize": 2,
                      "includes": includes, "bundle_files": 1,
                      }}

setup(
version = "0.1.0",
description = u"JD云服务PC模拟器",
name = "SmartCloud",
options = options,
zipfile = None,
windows = [{"script": "apps.py",
            "icon_resources": [(1, u"./ico/app.ico")]},
           {"script": "devs.py",
            "icon_resources": [(1, u"./ico/wifi.ico")]}
          ]
# windows = [{"script": "FormatTable.py"}]
)