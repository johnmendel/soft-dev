#!/usr/bin/env python

import time
import logging
from json import loads
from optparse import OptionParser
from contextlib import closing

from player import BreadcrumbPlayer, GreedyPlayer
from pexpect import spawn

# Get options from command line
parser = OptionParser()
parser.add_option("-l", "--larceny", dest="larceny", default="larceny",
                  help="Location of larceny binary", metavar="FILE")
parser.add_option("-g", "--game", dest="game", help="Location of game file")
parser.add_option("-c", "--charactertimeout", dest="character_timeout",
                  help="Time out for reading characters", type="float",
                  default=0.10)
parser.add_option("-r", "--responsetimeout", dest="response_timeout",
                  help="Timeout for total reading from shell", type="float",
                  default=4.00)
parser.add_option("-t", "--testcastle", dest="test_castle", metavar="FILE",
                  help="Run in test mode, with specified castle file")
parser.add_option("-d", "--debug", action='store_true', dest="debug",
                  default=False, help="Should we log DEBUG level information?")
parser.add_option("-i", "--info", dest="info", action='store_true',
                  default=False, help="Should we log INFO level information?")
parser.add_option("-s", "--random1", dest="random1", help="Random seed variable \
                  1", type="int")
parser.add_option("-q", "--random2", dest="random2", help="Random seed variable \
                  1", type="int")
parser.add_option("-p", "--player", dest="player", help="Player you want to use", \
                  default="BreadcrumbPlayer")
options, args = parser.parse_args()

# Get important options
character_timeout = options.character_timeout
response_timeout = options.response_timeout

# Determine if we are running our tester, or the actual game program
if options.test_castle:
    # Setup test file with specified castle
    process = "python dummy_game.py -c %s" % (options.test_castle)
else:
    # Make sure they specific a game
    if options.game == None:
        parser.error("Please specify a game location, see --help for details")
    # Setup command to execute program
    process = '%s -r6rs -program %s' % (options.larceny, options.game)
    
    if options.random1 and options.random2:
        process += ' -- outputfile %i %i' % (options.random1, options.random2)

# Setup the player
player = {'BreadcrumbPlayer' : BreadcrumbPlayer(),
          'GreedyPlayer' : GreedyPlayer()}[options.player]

# Setup logging
if options.debug or options.info:
    if options.debug:
        level = logging.DEBUG
    elif options.info:
        level = logging.INFO
    else:
        level = logging.WARN
    logging.basicConfig(level=level,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='./gamelog-%s.log' % int(time.time()),
                        filemode='w')

# Start process
with closing(spawn(process)) as child:

    # Send lines until you receive a False
    while True:
        # Get response
        response = child.receive_response(response_timeout, character_timeout)

        # Encode response
        # Strip first line for decoding, it's either the Version number or the last move
        response = response[response.find('\n') + 1:]

        # log the response
        logging.debug("Response:\n" + response)

        # Validate the response
        # blah here
        response = loads(response)

        # Determine next move and tell the game program
        next_move = player.handle_response(response)
        
        # If next_move is false then stop playing
        if next_move == False:
            break
        
        child.sendline(next_move)
