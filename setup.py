"""
Running this file will give you an 'example' .env file and some data
to start tinkering with.
"""

import os
import pandas as pd

parstring = '''
APPLANG=en
APPNAME=gottenso
FAMILY=braggingrights
PARENT=keep_track
CFILE=data/child_data.csv
GROFILE=curves_data.csv
P1FILE=data/p1_data.csv
P2FILE=data/p2_data.csv
LOGFILE=aux/logfile.txt
AGECOL=Age
COMCOL=Comment
DATECOL=Date
HEADCOL=Head_circumference
HEIGHTCOL=Height
WEIGHTCOL=Weight
SDWTCOL=sd_wt
SDHTCOL=sd_ht
CHILDBDAY=20210101
CHILDNAME=Charlie
MAX_AGE=3
P1BDAY=19810101
P1NAME=Alice
P2BDAY=19850505
P2NAME=Bob
'''

p_agevec = [0, 6, 12, 23, 45, 78]
p_heightvec = [53, 55, 59, 59, 61, 64]
p_weightvec = [3500, 3600, 3700, 3800, 4200, 4900]

c_agevec = [0, 3, 5, 9, 15, 16]
c_heightvec = [50, 51, 53, 56, 59, 60]
c_weightvec = [3700, 3750, 3800, 4000, 4200, 4356]
c_comments = ['Born here', '', 'Weight measured on produce scales', '', '', '']

parent = pd.DataFrame(data={'Age': p_agevec, 'Height': p_heightvec,
                            'Weight': p_weightvec})
child = pd.DataFrame(data={'Age': c_agevec, 'Height': c_heightvec,
                           'Weight': c_weightvec, 'Comment': c_comments})

if os.path.exists('.env'):
    os.rename('.env', '.env-old')

try:
    os.mkdir('data')
except FileExistsError:
    pass

parent.to_csv('data/p1_data.csv')
child.to_csv('data/child_data.csv')

with open('.env', 'w') as envfile:
    envfile.write(parstring)
