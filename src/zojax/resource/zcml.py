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
""" zojax:resource and zojax:directoryResource directives implementation

$Id$
"""
import os, posixpath

from zope import schema, interface
from zope.component.zcml import handler
from zope.component import getUtility, queryUtility

from zope.configuration import fields
from zope.configuration.exceptions import ConfigurationError

from zope.publisher.browser import BrowserView
from zope.publisher.interfaces import NotFound
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from zope.security.checker import CheckerPublic, NamesChecker

from zope.app.publisher.browser import metadirectives
from zope.app.publisher.browser.resource import Resource
from zope.app.publisher.browser.resources import empty
from zope.app.publisher.browser.resourcemeta import allowed_names
from zope.app.publisher.browser.directoryresource import Directory

from zojax.resource import fileresource
from zojax.resource.interfaces import IResourceFactory, IResourceFactoryType

_marker = object()


class IResourceDirective(metadirectives.IBasicResourceInformation):
    """ zojax:resource directive """

    name = schema.TextLine(
        title = u"The name of the resource",
        description = u"""
        This is the name used in resource urls. Resource urls are of
        the form site/@@/resourcename, where site is the url of
        "site", a folder with a site manager.

        We make resource urls site-relative (as opposed to
        content-relative) so as not to defeat caches.""",
        required = True)

    type = schema.TextLine(
        title = u'Resource type',
        required = False)

    file = fields.Path(
        title = u'Resource file',
        description = u'The file containing the resource data.',
        required = True)

# Arbitrary keys and values are allowed to be passed to the CustomWidget.
IResourceDirective.setTaggedValue('keyword_arguments', True)


class IResourceDirectoryDirective(metadirectives.IResourceDirectoryDirective):

    mapping = fields.Tokens(
        title = u'Resource mapping',
        description = u'By default resourceDirective tries determine resource '\
            u"type by it's extension, but we can define mapping explicitly."\
            u'Format ".{extention}:{resource type}" or "{filename}:{resource type}',
        required=False,
        value_type=schema.TextLine())


class IResourceDirectoryResourceType(interface.Interface):

    file = schema.TextLine(
        title = u'Filename',
        required = True)

    type = schema.TextLine(
        title = u'Resource type',
        required = True)


# Arbitrary keys and values are allowed to be passed to the CustomWidget.
IResourceDirectoryResourceType.setTaggedValue('keyword_arguments', True)


def resourceDirective(_context, name, file, layer=IDefaultBrowserLayer,
                      permission='zope.Public', type='', **kwargs):
    if permission == 'zope.Public':
        permission = CheckerPublic

    checker = NamesChecker(allowed_names, permission)

    _context.action(
        discriminator = ('zojax.resource', name, IBrowserRequest, layer),
        callable = resourceHandler,
        args = (name, layer, checker, file, type, _context.info),
        )


def resourceHandler(name, layer, checker, file, type, info):
    if type:
        factory = getUtility(IResourceFactoryType, name=type)
    else:
        type = os.path.splitext(os.path.normcase(name))[1][1:]

        factory = queryUtility(IResourceFactoryType, name=type)
        if factory is None:
            factory = getUtility(IResourceFactoryType)

    factory = factory(file, checker, name)

    handler('registerAdapter',
            factory, (layer,), interface.Interface, name, info)


class ResourceDirectoryDirective(object):


    def __init__(self, _context, name, directory, layer=IDefaultBrowserLayer,
                 permission='zope.Public', mapping=()):
        if permission == 'zope.Public':
            permission = CheckerPublic

        checker = NamesChecker(
            allowed_names + ('__getitem__', 'get'), permission)

        if not os.path.isdir(directory):
            raise ConfigurationError(
                "Directory %s does not exist" % directory)

        # process resource types
        types = {}
        for l in mapping:
            fname, type = l.split(':')
            info = {'file': None,
                    'ext': None,
                    'type': type}
            if fname[0] == '.':
                info['ext'] = fname[1:]
            else:
                info['file'] = fname
            types[fname] = info

        factory = DirectoryResourceFactory(directory, checker, name, types)
        _context.action(
            discriminator = ('zojax.resource', name, IBrowserRequest, layer),
            callable = handler,
            args = ('registerAdapter',
                    factory, (layer,), interface.Interface, name, _context.info))

        self.factory = factory

    def resourceType(self, _context, file, type, **kwargs):
        info = {'file': None,
                'ext': None,
                'type': type}
        info.update(kwargs)

        if file[0] == '.':
            info['ext'] = file[1:]
        else:
            info['file'] = file

        self.factory.types[file] = info


class DirectoryResource(BrowserView, Resource):

    interface.implements(IBrowserPublisher)

    default_factory = fileresource.filefactory

    types = {}

    def publishTraverse(self, request, name):
        '''See interface IBrowserPublisher'''
        return self.get(name)

    def browserDefault(self, request):
        '''See interface IBrowserPublisher'''
        return empty, ()

    def __getitem__(self, name):
        res = self.get(name, None)
        if res is None:
            raise KeyError(name)
        return res

    def get(self, name, default=_marker):
        request = self.request
        path = self.context.path
        filename = os.path.join(path, name)
        isfile = os.path.isfile(filename)
        isdir = os.path.isdir(filename)

        rname = posixpath.join(self.__name__, name)

        if not (isfile or isdir):
            if default is _marker:
                raise NotFound(self, name)
            return default

        if isfile:
            types = self.types

            info = types.get(name)
            if info is None:
                ext = os.path.splitext(os.path.normcase(name))[1]
                info = types.get(ext)

            if info is not None:
                if info['type'] == 'null':
                    raise NotFound(self, name)

                factoryType = queryUtility(IResourceFactoryType, name=info['type'])
                if factoryType is not None:
                    factory = factoryType(filename, self.context.checker, rname)

                    if IResourceFactory.providedBy(factory):
                        resource = factory(request, **info)
                    else:
                        resource = factory(request)

                    resource.__parent__ = self
                    return resource

            resource = self.default_factory(
                filename, self.context.checker, rname)(request)
        else:
            resource = DirectoryResourceFactory(
                filename, self.context.checker, rname, self.types)(request)

        resource.__parent__ = self
        return resource


class DirectoryResourceFactory(object):

    def __init__(self, path, checker, name, types={}):
        self._dir = Directory(path, checker, name)
        self._checker = checker
        self._name = name
        self.types = types

    def __call__(self, request):
        resource = DirectoryResource(self._dir, request)
        resource.__Security_checker__ = self._checker
        resource.__name__ = self._name
        resource.types = self.types
        return resource
