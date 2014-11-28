import logging
import socket

EOL = "\r\n"
END_OF_MOTD = "376"
BAD_NICKNAME = "432"

logging.basicConfig(level=logging.DEBUG)


def parsemsg(message_string):
    """Breaks a message from an IRC server into its prefix, command, arguments.
        http://stackoverflow.com/a/930706/1663352
    """

    prefix = ''
    trailing = []

    if not message_string:
        return "", "", ""

    if message_string[0] == ':':
        prefix, message_string = message_string[1:].split(' ', 1)

    if message_string.find(' :') != -1:
        message_string, trailing = message_string.split(' :', 1)
        args = message_string.split()
        args.append(trailing)
    else:
        args = message_string.split()
    command = args.pop(0)
    logging.debug("PREFIX: {0} COMMAND: {1} ARGS: {2}"
                  .format(prefix, command, args))
    return prefix, command, args


class SimpleBot(object):
    """ Simle IRC bot
    """

    def __init__(self, server='irc.freenode.org', port=6667, channel="#suckers",
                 name="NewBot", nick="NewBot"):
        self.name = name
        self.nick = nick
        self.server = server
        self.port = port
        self.chan = channel
        self.connection = None
        logging.debug("New Bot named {0} created for channel {1} on {2}"
                      .format(self.name, self.chan, self.server))

    def connect(self):
        """ Connect to given server """

        if self.connection:
            logging.warn("Connection already open please close before opening "
                         "another connection")
            return -1

        logging.info("Conncting to {0}".format(self.server))
        self.connection = socket.socket()

        try:
            self.connection.connect((self.server, self.port))
        except socket.error:
            logging.error("Failed to connect")
            self.connection = None

        if self.connection:
            self.sendHellos()
            self.loop()

    def loop(self):
        """ Main loop:
            TODO: COULD MAKE THIS RUN IN OWN THREAD
            TODO: POTENTIALLY SHOULD BE WAITING AFTER EACH COMMAND, CHECK THAT
        """
        line_buffer = ""  # String to hold incomming info
        try:
            while True:

                while EOL not in line_buffer:
                    # Try to slurp one line at a time
                    line_buffer += self.connection.recv(512)

                cur_ind = line_buffer.index(EOL)
                # The current line will be everything up to the first EOL
                line = line_buffer[:cur_ind]
                # everything else we're just going to throw back on the buffer
                line_buffer = line_buffer[cur_ind + 2:]  # +2 accounts for \r\n

                prefix, command, args = parsemsg(line)
                if command == "PING":
                    self.sendPong(args.pop())
                if command == END_OF_MOTD:
                    self.joinChannel()
                if command == BAD_NICKNAME:
                    logging.error("BAD NICK STOPPING BOT")
                    self.closeConnection("BAD NICK, PEACE OUT")
                    return

        except KeyboardInterrupt:
            logging.debug("KeyboardInerrupt, closing down")
            self.closeConnection("I'VE BEEN KILLED AVENGE ME")

    def writeLine(self, line):
        """ Everything should be calling this function to send stuff to server
        """
        self.connection.send(line + EOL)

    def sendHellos(self):
        """ Once connected to server setup name and nickname stuff """
        self.writeLine("NICK {0}".format(self.nick))
        self.writeLine("USER {0} {1} * :{2}"
                       .format(self.nick, socket.gethostname(), self.name))

    def sendPong(self, prefix):
        """ Sends PONG back to server """
        logging.debug("SENDING PONG TO {0}".format(prefix))
        self.writeLine("PONG {0}".format(prefix))

    def joinChannel(self):
        """" Join channel supplied on init """
        logging.debug("Joining: {0}".format(self.chan))
        self.writeLine("JOIN {0}".format(self.chan))

    def closeConnection(self, message="I'm off"):
        """ Close conecction with a optional message """
        logging.debug("Closing conecction")
        self.writeLine("QUIT :{0}".format(message))

if __name__ == '__main__':
    start_args = {
        "server": 'irc.freenode.org',
        "channel": '#turboburger',
        "nick": 'NoelBot',
        "name": "Noelbot",
    }
    ircbot = SimpleBot(**start_args)
    ircbot.connect()
