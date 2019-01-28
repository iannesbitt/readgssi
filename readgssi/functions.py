from datetime import datetime

def printmsg(msg):
    '''Prints with date/timestamp.'''
    print('%s - %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))