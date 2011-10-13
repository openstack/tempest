#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import gettext
import heapq
import os
import unittest
import sys
import time

from nose import config
from nose import result
from nose import core


class _AnsiColorizer(object):
    """
    A colorizer is an object that loosely wraps around a stream, allowing
    callers to write text to the stream in a particular color.

    Colorizer classes must implement C{supported()} and C{write(text, color)}.
    """
    _colors = dict(black=30, red=31, green=32, yellow=33,
                   blue=34, magenta=35, cyan=36, white=37)

    def __init__(self, stream):
        self.stream = stream

    def supported(cls, stream=sys.stdout):
        """
        A class method that returns True if the current platform supports
        coloring terminal output using this method. Returns False otherwise.
        """
        if not stream.isatty():
            return False  # auto color only on TTYs
        try:
            import curses
        except ImportError:
            return False
        else:
            try:
                try:
                    return curses.tigetnum("colors") > 2
                except curses.error:
                    curses.setupterm()
                    return curses.tigetnum("colors") > 2
            except:
                raise
                # guess false in case of error
                return False
    supported = classmethod(supported)

    def write(self, text, color):
        """
        Write the given text to the stream in the given color.

        @param text: Text to be written to the stream.

        @param color: A string label for a color. e.g. 'red', 'white'.
        """
        color = self._colors[color]
        self.stream.write('\x1b[%s;1m%s\x1b[0m' % (color, text))


class _Win32Colorizer(object):
    """
    See _AnsiColorizer docstring.
    """
    def __init__(self, stream):
        from win32console import GetStdHandle, STD_OUT_HANDLE, \
             FOREGROUND_RED, FOREGROUND_BLUE, FOREGROUND_GREEN, \
             FOREGROUND_INTENSITY
        red, green, blue, bold = (FOREGROUND_RED, FOREGROUND_GREEN,
                                  FOREGROUND_BLUE, FOREGROUND_INTENSITY)
        self.stream = stream
        self.screenBuffer = GetStdHandle(STD_OUT_HANDLE)
        self._colors = {
            'normal': red | green | blue,
            'red': red | bold,
            'green': green | bold,
            'blue': blue | bold,
            'yellow': red | green | bold,
            'magenta': red | blue | bold,
            'cyan': green | blue | bold,
            'white': red | green | blue | bold
            }

    def supported(cls, stream=sys.stdout):
        try:
            import win32console
            screenBuffer = win32console.GetStdHandle(
                win32console.STD_OUT_HANDLE)
        except ImportError:
            return False
        import pywintypes
        try:
            screenBuffer.SetConsoleTextAttribute(
                win32console.FOREGROUND_RED |
                win32console.FOREGROUND_GREEN |
                win32console.FOREGROUND_BLUE)
        except pywintypes.error:
            return False
        else:
            return True
    supported = classmethod(supported)

    def write(self, text, color):
        color = self._colors[color]
        self.screenBuffer.SetConsoleTextAttribute(color)
        self.stream.write(text)
        self.screenBuffer.SetConsoleTextAttribute(self._colors['normal'])


class _NullColorizer(object):
    """
    See _AnsiColorizer docstring.
    """
    def __init__(self, stream):
        self.stream = stream

    def supported(cls, stream=sys.stdout):
        return True
    supported = classmethod(supported)

    def write(self, text, color):
        self.stream.write(text)


def get_elapsed_time_color(elapsed_time):
    if elapsed_time > 1.0:
        return 'red'
    elif elapsed_time > 0.25:
        return 'yellow'
    else:
        return 'green'


class KongTestResult(result.TextTestResult):
    def __init__(self, *args, **kw):
        self.show_elapsed = kw.pop('show_elapsed')
        result.TextTestResult.__init__(self, *args, **kw)
        self.num_slow_tests = 5
        self.slow_tests = []  # this is a fixed-sized heap
        self._last_case = None
        self.colorizer = None
        # NOTE(vish, tfukushima): reset stdout for the terminal check
        stdout = sys.__stdout__
        sys.stdout = sys.__stdout__
        for colorizer in [_Win32Colorizer, _AnsiColorizer, _NullColorizer]:
            if colorizer.supported():
                self.colorizer = colorizer(self.stream)
                break
        sys.stdout = stdout

        # NOTE(lorinh): Initialize start_time in case a sqlalchemy-migrate
        # error results in it failing to be initialized later. Otherwise,
        # _handleElapsedTime will fail, causing the wrong error message to
        # be outputted.
        self.start_time = time.time()

    def getDescription(self, test):
        return str(test)

    def _handleElapsedTime(self, test):
        self.elapsed_time = time.time() - self.start_time
        item = (self.elapsed_time, test)
        # Record only the n-slowest tests using heap
        if len(self.slow_tests) >= self.num_slow_tests:
            heapq.heappushpop(self.slow_tests, item)
        else:
            heapq.heappush(self.slow_tests, item)

    def _writeElapsedTime(self, test):
        color = get_elapsed_time_color(self.elapsed_time)
        self.colorizer.write("  %.2f" % self.elapsed_time, color)

    def _writeResult(self, test, long_result, color, short_result, success):
        if self.showAll:
            self.colorizer.write(long_result, color)
            if self.show_elapsed and success:
                self._writeElapsedTime(test)
            self.stream.writeln()
        elif self.dots:
            self.stream.write(short_result)
            self.stream.flush()

    # NOTE(vish, tfukushima): copied from unittest with edit to add color
    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        self._handleElapsedTime(test)
        self._writeResult(test, 'OK', 'green', '.', True)

    # NOTE(vish, tfukushima): copied from unittest with edit to add color
    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        self._handleElapsedTime(test)
        self._writeResult(test, 'FAIL', 'red', 'F', False)

    # NOTE(vish, tfukushima): copied from unittest with edit to add color
    def addError(self, test, err):
        """Overrides normal addError to add support for errorClasses.
        If the exception is a registered class, the error will be added
        to the list for that class, not errors.
        """
        self._handleElapsedTime(test)
        stream = getattr(self, 'stream', None)
        ec, ev, tb = err
        try:
            exc_info = self._exc_info_to_string(err, test)
        except TypeError:
            # This is for compatibility with Python 2.3.
            exc_info = self._exc_info_to_string(err)
        for cls, (storage, label, isfail) in self.errorClasses.items():
            if result.isclass(ec) and issubclass(ec, cls):
                if isfail:
                    test.passwd = False
                storage.append((test, exc_info))
                # Might get patched into a streamless result
                if stream is not None:
                    if self.showAll:
                        message = [label]
                        detail = result._exception_detail(err[1])
                        if detail:
                            message.append(detail)
                        stream.writeln(": ".join(message))
                    elif self.dots:
                        stream.write(label[:1])
                return
        self.errors.append((test, exc_info))
        test.passed = False
        if stream is not None:
            self._writeResult(test, 'ERROR', 'red', 'E', False)

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)
        self.start_time = time.time()
        current_case = test.test.__class__.__name__

        if self.showAll:
            if current_case != self._last_case:
                self.stream.writeln(current_case)
                self._last_case = current_case

            self.stream.write(
                '    %s' % str(test.test._testMethodName).ljust(60))
            self.stream.flush()


class KongTestRunner(core.TextTestRunner):
    def __init__(self, *args, **kwargs):
        self.show_elapsed = kwargs.pop('show_elapsed')
        core.TextTestRunner.__init__(self, *args, **kwargs)

    def _makeResult(self):
        return KongTestResult(self.stream,
                              self.descriptions,
                              self.verbosity,
                              self.config,
                              show_elapsed=self.show_elapsed)

    def _writeSlowTests(self, result_):
        # Pare out 'fast' tests
        slow_tests = [item for item in result_.slow_tests
                      if get_elapsed_time_color(item[0]) != 'green']
        if slow_tests:
            slow_total_time = sum(item[0] for item in slow_tests)
            self.stream.writeln("Slowest %i tests took %.2f secs:"
                                % (len(slow_tests), slow_total_time))
            for elapsed_time, test in sorted(slow_tests, reverse=True):
                time_str = "%.2f" % elapsed_time
                self.stream.writeln("    %s %s" % (time_str.ljust(10), test))

    def run(self, test):
        result_ = core.TextTestRunner.run(self, test)
        if self.show_elapsed:
            self._writeSlowTests(result_)
        return result_


if __name__ == '__main__':
    show_elapsed = True
    argv = []
    for x in sys.argv:
        if x.startswith('test_'):
            argv.append('nova.tests.%s' % x)
        elif x.startswith('--hide-elapsed'):
            show_elapsed = False
        else:
            argv.append(x)

    c = config.Config(stream=sys.stdout,
                      env=os.environ,
                      verbosity=3,
                      plugins=core.DefaultPluginManager())

    runner = KongTestRunner(stream=c.stream,
                            verbosity=c.verbosity,
                            config=c,
                            show_elapsed=show_elapsed)
    sys.exit(not core.run(config=c, testRunner=runner, argv=argv))
