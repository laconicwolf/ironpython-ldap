#! ipy

__author__ = 'Jake Miller (@LaconicWolf)'
__date__ = '20181207'
__version__ = '0.01'
__description__ = '''Gets all users in a Domain.'''

import platform
if platform.python_implementation() != 'IronPython':
    print '\n[-] This script requires IronPython. Sorry!'
    exit()

import argparse
import os
import sys
import getpass

# Required to import .Net assemblies. CLR is Common Language Runtime
import clr

# Adds the assemblies to CLR. 
# CLR only includes a reference to System by default.
clr.AddReference("System.DirectoryServices")
clr.AddReference("System.DirectoryServices.AccountManagement")

# Importing the specific namespaces
from System.DirectoryServices import DirectorySearcher, DirectoryEntry, AccountManagement
from System.DirectoryServices.ActiveDirectory import DirectoryContext, DirectoryContextType, Domain
from System.Environment import UserDomainName

def getLdapUsers(domainController, ldapUsername, ldapPassword):
    """Authenticates to an LDAP server and returns a list of all 
    computer names.
    """
    ldapServer = 'LDAP://{}'.format(domainController)
    entry = DirectoryEntry(ldapServer, ldapUsername, ldapPassword)
    searcher = DirectorySearcher(entry)
    searcher.Filter = "(&(&(objectClass=user)(objectClass=person)))"
    searcher.SizeLimit = int.MaxValue
    searcher.PageSize = int.MaxValue
    results = searcher.FindAll()
    userNames = []
    for item in results:
        username = item.GetDirectoryEntry().Properties['samaccountname'].Value
        print username
        userNames.append(username)
    return userNames

def getDomainControllerName(domainName, ldapUsername, ldapPassword):
    """Authenticates to Active Directory and returns the name of the
    Domain Controller.
    """
    domainContext = DirectoryContext(DirectoryContextType.Domain, domainName, ldapUsername,ldapPassword)
    domainObj = Domain.GetDomain(domainContext)
    domainController = domainObj.FindDomainController()
    return domainController.Name

def main():
    """Queries LDAP to get all users in a Domain. Prints to the terminal
    and write to a file."""
    print '[*] Querying {}...'.format(domain)
    try:
        dcName = getDomainControllerName(domain, username, password)
    except Exception as e:
        print 'An error occurred: {}'.format(e)
        exit()
    print '[+] Successfully authenticated to {}. Querying all User Names:\n'.format(dcName)
    try:
        compNames = getLdapUsers(dcName, username, password)
    except Exception as e:
        print 'An error occurred: {}'.format(e)
        exit()
    outFileName = 'user_names_{}.txt'.format(domain.replace('.', '_'))
    with open(outFileName, 'w') as fh:
        for comp in compNames:
            fh.write(comp + '\n')
    print '[*] User names for {} written to {}.'.format(domain, outFileName)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Queries LDAP to get all users in a Domain. '
        'Prints to the terminal and write to a file.')
    )
    parser.add_argument(
        '-u', '--username',
        help='Specify a username to authenticate with.'
    )
    parser.add_argument(
        '-d', '--domain',
        help=('Specify a domain. Defaults to the local domain of the computer'
        ' the script is running from.')
    )
    parser.add_argument(
        '-p', '--password',
        help='Specify a password to authenticate with.'
    )
    args = parser.parse_args()

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
    
    if args.username:
        username = args.username
    else:
        username = raw_input('Username: ')
    if args.password:
        password = args.password
    else:
        password = getpass.getpass()
    if args.domain:
        domain = args.domain
    else:
        domain = UserDomainName
    main()