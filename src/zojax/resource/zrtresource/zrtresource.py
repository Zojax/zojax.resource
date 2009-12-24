##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id$
"""
from zope import interface
from zope.component.factory import Factory
from zope.app.component.hooks import getSite

from z3c.zrtresource.replace import Replace

from zojax.resource.interfaces import IResourceFactoryType
from zojax.resource.fileresource import File, FileResource

from processor import ExtZRTProcessor


class ZRTFileResource(FileResource):
    """ zrt resource """

    _commands_file = ''

    def index_html(self, *args):
        """ make ResourceRegistry happy """
        value = self.GET()
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        return value

    def render(self, request):
        file = self.chooseContext()
        f = open(file.path,'rb')
        data = f.read()
        f.close()
        p = ExtZRTProcessor(
            data, commands={'replace': Replace},
            commands_file = self._commands_file)
        return p.process(getSite(), self.request)

    def GET(self):
        """ default content """
        return self.render(self.request)


class ZRTFileResourceFactory(object):

    def __init__(self, path, checker, name, commands_file=''):
        self.__file = File(path, name)
        self.__checker = checker
        self.__name = name

        if not commands_file:
            if path.endswith('.zrt'):
                self.__commands_file = '%s.null'%path
            else:
                self.__commands_file = '%s.zrt'%path
        else:
            self.__commands_file = commands_file

    def __call__(self, request):
        resource = ZRTFileResource(self.__file, request)
        resource.__Security_checker__ = self.__checker

        name = self.__name
        if name.endswith('.zrt'):
            name = name[:-4]
        resource.__name__ = name
        resource._commands_file = self.__commands_file
        return resource


zrtfactory = Factory(ZRTFileResourceFactory)
interface.directlyProvides(zrtfactory, IResourceFactoryType)
