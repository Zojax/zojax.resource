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
from zope.app.publisher.fileresource import Image
from zope.app.publisher.fileresource import File as BaseFile
from zope.app.publisher.browser.fileresource import FileResource as BaseFileResource

from interfaces import IResource, IResourceFactoryType


class File(BaseFile):

    def __init__(self, path, name):
        super(File, self).__init__(path, name)

        if self.content_type == 'application/x-javascript':
            self.content_type = 'text/javascript'


class FileResource(BaseFileResource):
    interface.implements(IResource)

    def modified(self, default=long(0)):
        file = self.chooseContext()
        if getattr(file, 'lmt', None):
            return long(file.lmt)
        else:
            return default

    def render(self, request):
        file = self.chooseContext()
        f = open(file.path,'rb')
        data = f.read()
        f.close()
        return data


class FileResourceAdapter(object):
    interface.implements(IResource)

    def __init__(self, context):
        self.context = context

    def modified(self, default=long(0)):
        file = self.context.chooseContext()
        if getattr(file, 'lmt', None):
            return long(file.lmt)
        else:
            return default

    def render(self, request):
        file = self.context.chooseContext()
        f = open(file.path,'rb')
        data = f.read()
        f.close()
        return data


class FileResourceFactory(object):

    def __init__(self, path, checker, name):
        self._file = File(path, name)
        self._checker = checker
        self._name = name

    def __call__(self, request):
        resource = FileResource(self._file, request)
        resource.__Security_checker__ = self._checker
        resource.__name__ = self._name
        return resource


filefactory = Factory(FileResourceFactory)
interface.directlyProvides(filefactory, IResourceFactoryType)


class ImageResourceFactory(FileResourceFactory):

    def __init__(self, path, checker, name):
        self._file = Image(path, name)
        self._checker = checker
        self._name = name

imagefactory = Factory(ImageResourceFactory)
interface.directlyProvides(imagefactory, IResourceFactoryType)
