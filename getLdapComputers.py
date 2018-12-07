#! ipy

__author__ = 'Jake Miller (@LaconicWolf)'
__date__ = '20181207'
__version__ = '0.01'
__description__ = '''Gets all computers in a Domain.'''

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

def getLdapComputers(domainController, ldapUsername, ldapPassword):
    """Authenticates to an LDAP server and returns a list of all 
    computer names.
    """
    ldapServer = 'LDAP://{}'.format(domainController)
    entry = DirectoryEntry(ldapServer, ldapUsername, ldapPassword)
    searcher = DirectorySearcher(entry)
    searcher.Filter = ("(objectClass=computer)")
    searcher.SizeLimit = int.MaxValue
    searcher.PageSize = int.MaxValue
    results = searcher.FindAll()
    computerNames = []
    for item in results:
        if item.GetDirectoryEntry().Name.startswith('CN='):
            print str(item.GetDirectoryEntry().Name)[3:]
            computerNames.append(str(item.GetDirectoryEntry().Name)[3:])
    return computerNames

def getDomainControllerName(domainName, ldapUsername, ldapPassword):
    """Authenticates to Active Directory and returns the name of the
    Domain Controller.
    """
    domainContext = DirectoryContext(DirectoryContextType.Domain, domainName, ldapUsername,ldapPassword)
    domainObj = Domain.GetDomain(domainContext)
    domainController = domainObj.FindDomainController()
    return domainController.Name

def main():
    """Queries LDAP to get all computers in a Domain. Prints to the terminal
    and write to a file."""
    print '[*] Querying {}...'.format(domain)
    try:
        dcName = getDomainControllerName(domain, username, password)
    except Exception as e:
        print 'An error occurred: {}'.format(e)
        exit()
    print '[+] Successfully authenticated to {}. Querying all Computer Names:\n'.format(dcName)
    try:
        compNames = getLdapComputers(dcName, username, password)
    except Exception as e:
        print 'An error occurred: {}'.format(e)
        exit()
    outFileName = 'computer_names_{}.txt'.format(domain.replace('.', '_'))
    with open(outFileName, 'w') as fh:
        for comp in compNames:
            fh.write(comp + '\n')
    print '[*] Computer names for {} written to {}.'.format(domain, outFileName)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Queries LDAP to get all computers in a Domain. '
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