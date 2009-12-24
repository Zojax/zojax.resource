============================
``zojax:resource`` Directive
============================

This package provides a new directive similar to browser:resource directive.

  >>> from zope import component, interface
  >>> from zojax.resource import interfaces, fileresource

  >>> import zojax.resource
  >>> from zope.configuration import xmlconfig
  >>> context = xmlconfig.file('meta.zcml', zojax.resource)

Now we can register a resource:

  >>> import tempfile, os, os.path
  >>> fn = tempfile.mktemp('.js')
  >>> open(fn, 'w').write('''some resource data''')

  >>> context = xmlconfig.string('''
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:resource
  ...       name="resource.js"
  ...       file="%s" />
  ... </configure>
  ... '''%fn, context=context)

Now let's see whether the adapter has been registered:

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> response = request.response

  >>> resource = component.getAdapter(
  ...    request, interface.Interface, name='resource.js')

  >>> modified = resource.modified()

  >>> resource.render(request)
  'some resource data'

By default resource is FileResource

  >>> isinstance(resource.context, fileresource.File)
  True

We can set resource type explicitly

  >>> context = xmlconfig.string('''
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:resource
  ...       name="resource-image"
  ...       type="imageresource"
  ...       file="%s" />
  ... </configure>
  ... ''' %fn, context=context)

  >>> resource = component.getAdapter(
  ...    request, interface.Interface, name='resource-image')

  >>> isinstance(resource.context, fileresource.Image)
  True


Custom resource type
--------------------

We have to register IResourceFactoryType utility

  >>> from zojax.resource.tests import CustomFileResourceFactory
  >>> custom = component.factory.Factory(
  ...   CustomFileResourceFactory, interfaces=(interfaces.IResourceFactory,))
  >>> component.provideUtility(
  ...     custom, interfaces.IResourceFactoryType, name='custom')

  >>> context = xmlconfig.string('''
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:resource
  ...       name="resource-custom"
  ...       type="custom"
  ...       file="%s" />
  ... </configure>
  ... ''' %fn, context=context)

  >>> resource = component.getAdapter(
  ...    request, interface.Interface, name='resource-custom')

  >>> resource
  <zojax.resource.tests.CustomResource object at ...>

  >>> os.unlink(fn)


=====================================
``zojax:resourceDirectory`` Directive
=====================================

We need some temporary directories and files

  >>> import tempfile
  >>> dn = tempfile.mkdtemp()
  >>> os.mkdir(os.path.join(dn, 'subfolder'))
  >>> open(os.path.join(dn, 'resource1.css'), 'w').write('''\
  ... /* zrt-cssregistry: */ 
  ... h1 {
  ...   color: fontColor;
  ...   font: fontFamily;
  ...   background: url('../img1/mybackground.gif');
  ... }''')
  >>> open(os.path.join(dn, 'resource2.js'), 'w').write('test')
  >>> open(os.path.join(dn, 'resource3.css'), 'w').write('test')
  >>> open(os.path.join(dn, 'resource4.jpg'), 'w').write('test')
  >>> open(os.path.join(dn, 'resource5.png'), 'w').write('test')

Directive require directory path

  >>> context = xmlconfig.string('''
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:resourcedirectory
  ...       name="myresources"
  ...       directory="%s" />
  ... </configure>
  ... ''' %(dn+'123123234534234'), context=context)
  Traceback (most recent call last):
  ...
  ZopeXMLConfigurationError: ...

Now we can register a directory of resources, also we can set
resource types:

  >>> context = xmlconfig.string('''
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:resourcedirectory
  ...       name="myresources"
  ...       directory="%s"
  ...	    mapping=".css:zrt .js:fileresource
  ...                resource3.css:cutom .png:null" />
  ... </configure>
  ... ''' %dn, context=context)

  >>> dirresource = component.getAdapter(
  ...    request, interface.Interface, name='myresources')

Now we can get resource

  >>> dirresource.browserDefault(request)
  (<function empty at ...>, ())

  >>> resource = dirresource.publishTraverse(request, 'resource1.css')
  >>> print resource.GET()
  h1 {
      color: #11111111;
      font: Verdana;
      background: url('../img1/mybackground.gif');
  }

  >>> print dirresource['resource1.css'].GET()
  h1 {
      color: #11111111;
      font: Verdana;
      background: url('../img1/mybackground.gif');
  }

  >>> dirresource.publishTraverse(request, 'unknown.css')
  Traceback (most recent call last):
  ...
  NotFound: ...

  >>> dirresource['unknown.css']
  Traceback (most recent call last):
  ...
  KeyError: 'unknown.css'


Types mapping
-------------

  In 'mapping' we defined that all files with '.css' extension should be 
custom type, '.js' should be file resource and filename 'test.css' 
should be file resource, '.png' should be not available

  >>> dirresource.publishTraverse(request, 'resource1.css')
  <zojax.resource.zrtresource.zrtresource.ZRTFileResource ...>

  >>> dirresource.publishTraverse(request, 'resource2.js')
  <zojax.resource.fileresource.FileResource object at ...>

  >>> dirresource.publishTraverse(request, 'resource3.css')
  <zojax.resource.fileresource.FileResource object at ...>

  >>> dirresource.publishTraverse(request, 'resource4.jpg')
  <zojax.resource.fileresource.FileResource object at ...>

  >>> dirresource.publishTraverse(request, 'resource5.png')
  Traceback (most recent call last):
  ...
  NotFound: Object: ...

Or we can use 'resourceType' subdirective:

  >>> context = xmlconfig.string('''
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:resourcedirectory
  ...       name="myresources2"
  ...       directory="%s">
  ...     <resourceType file=".css" type="zrt" />
  ...     <resourceType file=".js" type="fileresource" />
  ...     <resourceType file="resource3.css" type="custom" />
  ...     <resourceType file=".png" type="null" />
  ...   </zojax:resourcedirectory>
  ... </configure>
  ... ''' %dn, context=context)

  >>> dirresource = component.getAdapter(
  ...    request, interface.Interface, name='myresources2')

  >>> dirresource.publishTraverse(request, 'resource1.css')
  <zojax.resource.zrtresource.zrtresource.ZRTFileResource ...>

  >>> dirresource.publishTraverse(request, 'resource2.js')
  <zojax.resource.fileresource.FileResource object at ...>

  >>> dirresource.publishTraverse(request, 'resource3.css')
  <zojax.resource.tests.CustomResource object at ...>

  >>> dirresource.publishTraverse(request, 'resource4.jpg')
  <zojax.resource.fileresource.FileResource object at ...>

  >>> dirresource.publishTraverse(request, 'resource5.png')
  Traceback (most recent call last):
  ...
  NotFound: Object: ...


We can get sub directories

  >>> subdir = dirresource.publishTraverse(request, 'subfolder')


  >>> os.unlink(os.path.join(dn, 'resource1.css'))
  >>> os.unlink(os.path.join(dn, 'resource2.js'))
  >>> os.unlink(os.path.join(dn, 'resource3.css'))
  >>> os.unlink(os.path.join(dn, 'resource4.jpg'))
  >>> os.unlink(os.path.join(dn, 'resource5.png'))
  >>> os.rmdir(os.path.join(dn, 'subfolder'))
  >>> os.rmdir(dn)
