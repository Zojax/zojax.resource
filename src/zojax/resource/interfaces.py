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
from zojax.cacheheaders.interfaces import IModificationInfo


class IResource(IModificationInfo):

    def render(request):
        """ render resource """


class IResourceFactory(interface.Interface):

    def __call__(self, request, **kwargs):
        """ create resource """


class IResourceFactoryType(interface.Interface):

    def __call__(self, path, checker, name):
        """ create resource factory """
