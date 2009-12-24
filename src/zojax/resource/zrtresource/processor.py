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
import re
from zope.component import queryUtility

from z3c.zrtresource.processor import ZRTProcessor, COMMAND_REGEX, COMMAND, TEXTBLOCK
from z3c.zrtresource.interfaces import IZRTCommand, IZRTCommandFactory, UnknownZRTCommand

EXTERNAL_COMMAND = 2


class ExtZRTProcessor(ZRTProcessor):
    """A ZRT Processor"""

    def __init__(self, source, commands=None, commands_file=''):
        super(ExtZRTProcessor, self).__init__(source, commands)
        self.commands_file = commands_file


    def compile(self):
        """See interfaces.IZRTProcessor"""
        # get extra commands from external file
        extra = ''
        try:
            if bool(self.commands_file):
                extra = open(self.commands_file, 'r').read() + '\n'
        except IOError:
            pass

        bytecode = []
        pos = 0

        regex = re.compile(COMMAND_REGEX %(self.commandStartRegex,self.commandEndRegex))

        # Find all commands
        for match in regex.finditer(self.source):
            command, args = match.groups()

            # Add the previous text block and update position
            bytecode.append((TEXTBLOCK, self.source[pos:match.start()]))
            pos = match.end() + 1

            # Make sure the command exists
            if command not in self.commands:
                cmd = queryUtility(IZRTCommandFactory, command)

                if cmd is None:
                    raise UnknownZRTCommand(command)

                # Add the command
                bytecode.append((EXTERNAL_COMMAND,
                                 (cmd, args, match.start(), match.end())))
            else:
                # Add the command
                bytecode.append((COMMAND,
                                 (command, args, match.start(), match.end())))

        # Add the final textblock
        bytecode.append((TEXTBLOCK, self.source[pos:]))

        self._bytecode = bytecode

        bytecode = []
        pos = 0

        # Find all commands
        for match in regex.finditer(extra):
            command, args = match.groups()

            # Add the previous text block and update position
            pos = match.end() + 1

            # Make sure the command exists
            if command not in self.commands:
                cmd = queryUtility(IZRTCommandFactory, command)

                if cmd is None:
                    raise UnknownZRTCommand(command)

                # Add the command
                bytecode.append((EXTERNAL_COMMAND,
                                 (cmd, args, match.start(), match.end())))
            else:
                # Add the command
                bytecode.append((COMMAND,
                                 (command, args, match.start(), match.end())))


        self._bytecode = bytecode + self._bytecode
