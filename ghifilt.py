"""
Exports issues from a list of repositories to individual csv files.
Uses basic authentication (Github username + password) to retrieve issues
from a repository that username has access to. Supports Github API v3.
Forked from: unbracketed/export_repo_issues_to_csv.py
https://gist.github.com/patrickfuller/e2ea8a94badc5b6967ef3ca0a9452a43
"""
import argparse
import csv
from getpass import getpass
import requests
from datetime import datetime, date

auth = None
state = 'open'
lbl = ''
now = datetime.now()
# nowstr=str(now)
nowdate = str(now.date())


def write_issues(r, csvout):
    """Parses JSON response and writes to CSV."""
    if r.status_code != 200:
        raise Exception(r.status_code)
    for issue in r.json():
        if 'pull_request' not in issue:
            labels = ', '.join([l['name'] for l in issue['labels']])
            assignees = ', '.join([a['login'] for a in issue['assignees']])
            
            if not issue['milestone'] == None:
                milestone = issue['milestone']['title']
            else:
                milestone = "No Milestone"    

            # removing time from github date columns
            createddate = issue['created_at'].split('T')[0]
            updateddate = issue['updated_at'].split('T')[0]

            # get days to determine issue to calculate age
            date_format = "%Y-%m-%d"
            a = datetime.strptime(createddate, date_format)
            b = datetime.strptime(updateddate, date_format)
            c = datetime.strptime(nowdate, date_format)

            # check close date is not null
            if not issue['closed_at'] == None:
                closeddate = issue['closed_at'].split('T')[0]
                #convert closedate to the necessary format for age calculation
                cd = datetime.strptime(closeddate, date_format)
                age = (cd-a).days
            else:
                # Automate close date population for all open issues with next year dec date
                closeddate = date((now.year)+1, 12, 31)
                age = (c-a).days

            # Write out additional fields
            # csvout.writerow([issue['number'],labels, assignees, issue['title'], issue['body'], issue['state'], createddate, updateddate, closeddate,age,
            #                 issue['html_url']])
            csvout.writerow([issue['number'], labels, assignees, issue['title'], issue['state'], createddate, updateddate, closeddate, age, milestone,
                            issue['html_url']])


def get_issues(name, lbl):
    """Requests issues from GitHub API and writes to CSV file."""
    url = 'https://api.github.com/repos/{}/issues?state={}&labels={}'.format(name, state, lbl)
    r = requests.get(url, auth=auth)

    # custom format file name to include date.
    csvnameformat = '{}-issues-'.format(name.replace('/', '-'))

    # check if there are no comma seperated lables and replace string with all
    if "," not in lbl:
        lblformat = lbl.replace(" ", "all")
    else:
        lblformat = lbl.replace(" ", "_").replace(",", "-")

    # format filename to include organization-reponame-issues-date-labels-extenssion
    csvfilename = csvnameformat + nowdate + '-' + lblformat + '.csv'

    with open(csvfilename, 'w', newline='') as csvfile:
        csvout = csv.writer(csvfile)
        # Create csv file and write the headers
        csvout.writerow(['Number', 'Labels', 'Assignees', 'Title', 'State',
                         'Created Date', 'Updated Date', 'Closed Date', 'Age','Milestone', 'URL'])
        
        write_issues(r, csvout)

        # Multiple requests are required if response is paged
        if 'link' in r.headers:
            pages = {rel[6:-1]: url[url.index('<')+1:-1] for url, rel in
                     (link.split(';') for link in
                      r.headers['link'].split(','))}
            while 'last' in pages and 'next' in pages:
                pages = {rel[6:-1]: url[url.index('<')+1:-1] for url, rel in
                         (link.split(';') for link in
                          r.headers['link'].split(','))}
                r = requests.get(pages['next'], auth=auth)
                write_issues(r, csvout)
                if pages['next'] == pages['last']:
                    break


# Parse input parameters
parser = argparse.ArgumentParser(description="Write GitHub repository issues "
                                             "to CSV file.")
parser.add_argument('repositories', nargs='+', help="Repository names, "
                    "formatted as 'username/repo'")
parser.add_argument('--all', action='store_true', help="Returns both open "
                    "and closed issues.")
parser.add_argument(
    'lbl', help="Comma seperated labels example : bug,question,'help wanted' . for all labels pass space in empty brackets ")
args = parser.parse_args()

if args.all:
    state = 'all'

username = input("Username for 'https://github.com': ")
password = getpass("Password for 'https://{}@github.com': ".format(username))
auth = (username, password)
for repository in args.repositories:
    get_issues(repository, args.lbl)
