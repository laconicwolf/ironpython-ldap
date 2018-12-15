#! ipy

__author__ = 'Jake Miller (@LaconicWolf)'
__date__ = '20181128'
__version__ = '0.01'
__description__ = '''A multithreaded program to get the members of specified groups'''

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
from System.DirectoryServices.AccountManagement import UserPrincipal, GroupPrincipal
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

def getGroupMembers(principalContext, ldapGroupname):
    """Requires a group name and principal context. Returns a 
    dictionary where the key is the group name and the value is 
    a list of group members.
    """
    group = GroupPrincipal.FindByIdentity(principalContext, ldapGroupname)
    allMembers = group.GetMembers(True)
    memberList = [member.SamAccountName for member in allMembers]
    results[ldapGroupname] = memberList

def manageQueue():
    """Manages the group queue, passing each group to the 
    getGroupMembers function.
    """
    context = getPrincipalContext(domain, ldapUser, ldapPass)
    while True:
        currentGroup = groupQueue.get()
        #print '[*] Getting users for {}'.format(currentGroup)
        getGroupMembers(context, currentGroup)
        groupQueue.task_done()

def main():
    """Starts the multithreading."""
    for i in range(args.threads):
        t = threading.Thread(target=manageQueue)
        t.daemon = True
        t.start()
    for currentGroup in groupnames:
        groupQueue.put(currentGroup)
    groupQueue.join()
    print
    for item in results:
        print item
        for username in results[item]:
            print "  {}".format(username)

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
        '-gf', '--groupname_file',
        help='Specify the path of a file containing groupnames to get associated users.'
    )
    parser.add_argument(
        '-g', '--groupname',
        help='Specify a single groupname to get associated users.'
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

    if not args.groupname and not args.groupname_file:
        parser.print_help()
        print ('\n[-] Please specify either a single groupname (-g) or the '
        'path to a file listing groupnames (-gf).')
        exit()
    if args.groupname and args.groupname_file:
        parser.print_help()
        print ('\n[-] Please specify either a single groupname (-g) or the '
        'path to a file listing groupnames (-gf). Not both.')
        exit()
    if args.groupname:
        groupnames = [args.groupname]
    if args.groupname_file:
        if not os.path.exists(args.groupname_file):
            print ('\n[-] The file {} does not exist or you do not have '
            'access to it. Please check the path and try again.'.format(
                args.groupname_file))
            exit()
        with open(args.groupname_file) as fh:
            groupnames = fh.read().splitlines()

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
    groupQueue = Queue.Queue()

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