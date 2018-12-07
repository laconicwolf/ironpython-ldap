#! ipy

__author__ = 'Jake Miller (@LaconicWolf)'
__date__ = '20181128'
__version__ = '0.01'
__description__ = '''A multithreaded program to get the groups of specified user(s)'''

import platform
if platform.python_implementation() != 'IronPython':
    print '\n[-] This script requires IronPython. Sorry!'
    exit()

import argparse
import os
import sys
import threading
import Queue
import getpass

# Required to import .Net assemblies. CLR is Common Language Runtime
import clr

# Adds the assemblies to CLR. 
# CLR only includes a reference to System by default.
clr.AddReference("System.DirectoryServices.AccountManagement")

# Importing the specific namespaces
from System.DirectoryServices import AccountManagement
from System.DirectoryServices.AccountManagement import UserPrincipal
from System.Environment import UserDomainName

def getPrincipalContext(domainName, ldapUsername, ldapPassword):
    """Attempts to authenticate using a specified username,
    password, and domain.
    """
    try:
        principalContext = AccountManagement.PrincipalContext(
            AccountManagement.ContextType.Domain, domainName,
            ldapUsername, ldapPassword
        )
    except Exception as e:
        print '[-] An error has occurred: {}'.format(e)
        exit()
    return principalContext

def getUserGroup(principalContext, ldapUsername):
    """Requires a username and principal context. Returns a dictionary
    where the key is the user and the value is a list of groups.
    """
    user = UserPrincipal.FindByIdentity(principalContext, ldapUsername)
    groups = user.GetGroups()
    groupList = [group.Name for group in groups]
    results[ldapUsername] = groupList

def manageQueue():
    """Manages the username queue, passing each user to the 
    guessLdapCreds function.
    """
    context = getPrincipalContext(domain, ldapUser, ldapPass)
    while True:
        currentUser = userQueue.get()
        #print '[*] Getting groups for {}'.format(currentUser)
        getUserGroup(context, currentUser)
        userQueue.task_done()

def main():
    """Starts the multithreading."""
    for i in range(args.threads):
        t = threading.Thread(target=manageQueue)
        t.daemon = True
        t.start()
    for currentUser in usernames:
        userQueue.put(currentUser)
    userQueue.join()
    print
    for item in results:
        print item
        for groupname in results[item]:
            print "  {}".format(groupname)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Get the groupnames associated with a list of users.'
    )
    parser.add_argument(
        '-au', '--authusername',
        help='Specify a username to authenticate with.'
    )
    parser.add_argument(
        '-d', '--domain',
        help=('Specify a domain. Defaults to the local domain of the computer'
        ' the script is running from.')
    )
    parser.add_argument(
        '-ap', '--authpassword',
        help='Specify a password to authenticate with.'
    )
    parser.add_argument(
        '-uf', '--username_file',
        help='Specify the path of a file containing usernames to get associated groups.'
    )
    parser.add_argument(
        '-u', '--username',
        help='Specify a single username to get associated groups.'
    )
    parser.add_argument(
        "-t", "--threads",
        nargs="?",
        type=int,
        const=5,
        default=5,
        help="Specify number of threads (default=5)"
    )
    args = parser.parse_args()

    if not args.username and not args.username_file:
        parser.print_help()
        print ('\n[-] Please specify either a single username (-u) or the '
        'path to a file listing usernames (-uf).')
        exit()
    if args.username and args.username_file:
        parser.print_help()
        print ('\n[-] Please specify either a single username (-u) or the '
        'path to a file listing usernames (-uf). Not both.')
        exit()
    if args.username:
        usernames = [args.username]
    if args.username_file:
        if not os.path.exists(args.username_file):
            print ('\n[-] The file {} does not exist or you do not have '
            'access to it. Please check the path and try again.'.format(
                args.username_file))
            exit()
        with open(args.username_file) as fh:
            usernames = fh.read().splitlines()

    if args.authusername:
        ldapUser = args.authusername
    else:
        ldapUser = raw_input('Username for authentication: ')
    if args.authpassword:
        ldapPass = args.authpassword
    else:
        ldapPass = getpass.getpass()
    if args.domain:
        domain = args.domain
    else:
        domain = UserDomainName

    printLock = threading.Lock()
    userQueue = Queue.Queue()

    # Global dictionary to store the results
    results = {}

    word_banner = '{} version: {}. Coded by: {}'.format(
        sys.argv[0], __version__, __author__)
    print('=' * len(word_banner))
    print(word_banner)
    print('=' * len(word_banner))
    print
    for arg in vars(args):
        if getattr(args, arg):
            print('{}: {}'.format(
                arg.title().replace('_',' '), getattr(args, arg)))
    print
    main()