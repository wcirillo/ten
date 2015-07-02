"""
Webkit2png
"""
#pylint: disable=C0103,W0622
#!/usr/bin/env python
#
# webkit2png.py
#
# Creates screenshots of webpages using by QtWebkit.
#
# Copyright (c) 2008 Roland Tapken <roland@dau-sicher.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
# Nice ideas "todo":
# - Add QTcpSocket support to create a "screenshot daemon" that
# can handle multiple requests at the same time.

import sys
import os
import logging
import time

from PyQt4.QtCore import QObject, SIGNAL, Qt, QUrl, QCoreApplication, \
    QBuffer
from PyQt4.QtGui import QApplication, QMainWindow, QPixmap
from PyQt4.QtWebKit import QWebSettings, QWebPage, QWebView

VERSION = "20091224"
LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


# Class for Website-Rendering. Uses QWebPage, which
# requires a running QtGui to work.
class WebkitRenderer(QObject):
    """
    A class that helps to create 'screenshots' of webpages using
    Qt's QWebkit. Requires PyQt4 library.

    Use "render()" to get a 'QImage' object, render_to_bytes() to get the
    resulting image as 'str' object or render_to_file() to write the image
    directly into a 'file' resource.

    These methods have to be called from within Qt's main (GUI) thread.
    An example on how to use this is the __qt_main() method at the end
    of the libraries source file. More generic examples:

    def qt_main():
    while go_on():
    do_something_meaningful()
    while QApplication.hasPendingEvents():
    QApplication.processEvents()
    QApplication.quit()

    app = init_qtgui()
    QTimer.singleShot(0, qt_main)
    sys.exit(app.exec_())

    Or let Qt handle event processing using a QTimer instance:

    def qt_main_loop():
    if not go_on():
    QApplication.quit()
    return
    do_something_meaningful()
    app = init_qtgui()
    main_timer = QTimer()
    QObject.connect(main_timer, QtCore.SIGNAL("timeout()"), qt_main_loop)
    sys.exit(app.exec_())

    Avaible properties:
    width -- The width of the "browser" window. 0 means autodetect (default).
    height -- The height of the window. 0 means autodetect (default).
    timeout -- Seconds after that the request is aborted (default: 0)
    wait -- Seconds to wait after loading has been finished (default: 0)
    scaleToWidth -- The resulting image is scaled to this width.
    scaleToHeight -- The resulting image is scaled to this height.
    scaleRatio -- The image is scaled using this method. Possible values are:
    keep
    expand
    crop
    ignore
    grabWhileWindow -- If this is True a screenshot of the whole window is 
        taken. Otherwise only the current frame is rendered. This is required 
        for plugins to be visible, but it is possible that another window 
        overlays the current one while the screenshot is taken. To reduce this 
        possibility, the window is activated just before it is rendered if this 
        property is set to True (default: False).
    qWebSettings -- Settings that should be assigned to the created QWebPage 
        instance. See http://doc.trolltech.com/4.6/qwebsettings.html for 
        possible keys. Defaults:
    JavascriptEnabled: False
    PluginsEnabled: False
    PrivateBrowsingEnabled: True
    JavascriptCanOpenWindows: False
"""
    os.putenv('DISPLAY',':15')
    def __init__(self, **kwargs):
        """ Sets default values for the properties. """

        if not QApplication.instance():
            raise RuntimeError(self.__class__.__name__ + " requires a running QApplication instance")
        QObject.__init__(self)

        # Initialize default properties
        self.width = kwargs.get('width', 0)
        self.height = kwargs.get('height', 0)
        self.timeout = kwargs.get('timeout', 0)
        self.wait = kwargs.get('wait', 0)
        self.scaleToWidth = kwargs.get('scaleToWidth', 0)
        self.scaleToHeight = kwargs.get('scaleToHeight', 0)
        self.scaleRatio = kwargs.get('scaleRatio', 'keep')
        # Set this to true if you want to capture flash.
        # Not that your desktop must be large enough for
        # fitting the whole window.
        self.grabWholeWindow = kwargs.get('grabWholeWindow', True)
        
        # Set some default options for QWebPage
        self.qWebSettings = {
            QWebSettings.JavascriptEnabled : True,
            QWebSettings.PluginsEnabled : True,
            QWebSettings.PrivateBrowsingEnabled : True,
            QWebSettings.JavascriptCanOpenWindows : False
        }

    def render(self, url):
        """ Renders the given URL into a QImage object. """
        # We have to use this helper object because
        # QApplication.processEvents may be called, causing
        # this method to get called while it has not returned yet.
        helper = _WebkitRendererHelper(self)
        image = helper.render(url)

        # Bind helper instance to this image to prevent the
        # object from being cleaned up (and with it the QWebPage, etc)
        # before the data has been used.
        image.helper = helper

        return image

    def render_to_file(self, url, file):
        """
        Renders the image into a File resource.
        Returns the size of the data that has been written.
        """ 
        format = self.format # this may not be constant due to processEvents()
        image = self.render(url)
        qBuffer = QBuffer()
        image.save(qBuffer, format)
        file.write(qBuffer.buffer().data())
        return qBuffer.size()

    def render_to_bytes(self, url):
        """ Renders the image into an object of type 'str'. """
        format = self.format # this may not be constant due to processEvents()
        image = self.render(url)
        qBuffer = QBuffer()
        image.save(qBuffer, format)
        return qBuffer.buffer().data()

class _WebkitRendererHelper(QObject):
    """
    This helper class is doing the real work. It is required to allow 
    WebkitRenderer.render() to be called "asynchronously"
    (but always from Qt's GUI thread).
    """

    def __init__(self, parent):
        """
        Copies the properties from the parent (WebkitRenderer) object,
        creates the required instances of QWebPage, QWebView and QMainWindow
        and registers some Slots.
        """
        QObject.__init__(self)

        # Copy properties from parent
        for key, value in parent.__dict__.items():
            setattr(self, key, value)

        # Create and connect required PyQt4 objects
        self._page = QWebPage()
        self._view = QWebView()
        self._view.setPage(self._page)
        self._window = QMainWindow()
        self._window.setCentralWidget(self._view)

        # Import QWebSettings
        for key, value in self.qWebSettings.iteritems():
            self._page.settings().setAttribute(key, value)

        # Connect required event listeners
        self.connect(self._page, SIGNAL("loadFinished(bool)"), self._on_load_finished)
        self.connect(self._page, SIGNAL("loadStarted()"), self._on_load_started)
        self.connect(self._page.networkAccessManager(), SIGNAL("sslErrors(QNetworkReply *,const QList<QSslError>&)"), self._on_ssl_errors)

        # The way we will use this, it seems to be unesseccary to have Scrollbars enabled
        self._page.mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self._page.mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self._page.settings().setUserStyleSheetUrl(QUrl("data:text/css,html,body{overflow-y:hidden !important;}"))
        
        # Show this widget
        self._window.show()

    def __del__(self):
        """Clean up Qt4 objects. """
        self._window.close()
        del self._window
        del self._view
        del self._page

    def render(self, url):
        """The real worker. Loads the page (_load_page) and awaits
        the end of the given 'delay'. While it is waiting outstanding
        QApplication events are processed.
        After the given delay, the Window or Widget (depends
        on the value of 'grabWholeWindow' is drawn into a QPixmap
        and postprocessed (_post_process_image).
        """
        self._load_page(url, self.width, self.height, self.timeout)
        # Wait for end of timer. In this time, process
        # other outstanding Qt events.
        if self.wait > 0:
            LOG.debug("Waiting %d seconds " % self.wait)
            waitToTime = time.time() + self.wait
            while time.time() < waitToTime:
                while QApplication.hasPendingEvents():
                    QApplication.processEvents()

        # Paint this frame into an image
        #self._window.repaint()
        while QApplication.hasPendingEvents():
            QApplication.processEvents()
        
        if self.grabWholeWindow:
            # Note that this does not fully ensure that the
            # window still has the focus when the screen is
            # grabbed. This might result in a race condition.
            self._view.activateWindow()
            image = QPixmap.grabWindow(self._window.winId())
        else:
            image = QPixmap.grabWidget(self._window)

        ## Another possible drawing solution
        #image = QImage(self._page.viewportSize(), QImage.Format_ARGB32)
        #painter = QPainter(image)
        #self._page.mainFrame().render(painter)
        #painter.end()

        return self._post_process_image(image)

    def _load_page(self, url, width, height, timeout):
        """
        This method implements the logic for retrieving and displaying
        the requested page.
        """
        # This is an event-based application. So we have to wait until
        # "loadFinished(bool)" raised.
        cancelAt = time.time() + timeout
        self.__loadings = True
        self.__loadingResult = False # Default
        # TODO: fromEncoded() needs to be used in some situations. Some
        # sort of flag should be passed in to WebkitRenderer maybe?
        #self._page.mainFrame().load(QUrl.fromEncoded(url))

        self._page.mainFrame().load(QUrl(url))
        while self.__loadings:
            if timeout > 0 and time.time() >= cancelAt:
                raise RuntimeError("Request timed out on %s" % url)
            while QApplication.hasPendingEvents():
                QCoreApplication.processEvents()

        LOG.debug("Processing result")

        if self.__loading_result == False:
            LOG.warning("Failed to load %s" % url)

        # Set initial viewport (the size of the "window")
        size = self._page.mainFrame().contentsSize()
        LOG.debug("contentsSize: %s", size)
        if width > 0:
            size.setWidth(width)
        if height > 0:
            size.setHeight(height)

        self._window.resize(size)

    def _post_process_image(self, q_image):
        """
        If 'scaleToWidth' or 'scaleToHeight' are set to a value greater than 
        zero this method will scale the image using the method defined in 
        'scaleRatio'.
        """
        if self.scaleToWidth > 0 or self.scaleToHeight > 0:
            # Scale this image
            if self.scaleRatio == 'keep':
                ratio = Qt.KeepAspectRatio
            elif self.scaleRatio in ['expand', 'crop']:
                ratio = Qt.KeepAspectRatioByExpanding
            else: # 'ignore'
                ratio = Qt.IgnoreAspectRatio
            q_image = q_image.scaled(self.scaleToWidth, self.scaleToHeight, ratio)
            if self.scaleRatio == 'crop':
                q_image = q_image.copy(0, 0, self.scaleToWidth, self.scaleToHeight)
        return q_image

    # Eventhandler for "loadStarted()" signal
    def _on_load_started(self):
        """ Slot that sets the '__loading' property to true. """
        LOG.debug("loading started")
        self.__loadings = True

    # Eventhandler for "loadFinished(bool)" signal
    def _on_load_finished(self, result):
        """
        Slot that sets the '__loading' property to false and stores
        the result code in '__loading_result'.
        """
        LOG.debug("loading finished with result %s", result)
        self.__loadings = False
        self.__loading_result = result

    # Eventhandler for "sslErrors(QNetworkReply *,const QList<QSslError>&)" signal
    def _on_ssl_errors(self, reply, errors):
        """ Slot that writes SSL warnings into the log but ignores them. """
        for e in errors:
            LOG.warn("SSL: " + e.errorString())
        reply.ignoreSslErrors()


def init_qtgui(display=15, style=None, qtargs=[]):
    """Initiates the QApplication environment using the given arguments."""
    if QApplication.instance():
        LOG.debug("QApplication has already been instantiated. \
Ignoring given arguments and returning existing QApplication.")
        return QApplication.instance()
    
    qtargs2 = [sys.argv[0]]
    display = 15
    if display:
        qtargs2.append('-display')
        qtargs2.append(display)
        # Also export DISPLAY var as this may be used
        # by flash plugin
        os.environ["DISPLAY"] = display
    
    if style:
        qtargs2.append('-style')
        qtargs2.append(style)
    
    qtargs2.extend(qtargs)
    
    return QApplication(qtargs2)
