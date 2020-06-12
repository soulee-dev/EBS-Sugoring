import ondl
import json
import os
from urllib.parse import parse_qsl

version = '1.0.0'

if os.path.isfile('config.json'):
    with open('config.json', 'r') as f:
        json_data = json.load(f)
else:
    config = dict()
    config['id'] = input('ID : ')
    config['pw'] = input('PW : ')
    config['prefix'] = input('Prefix : ')
    config['schoolid'] = input('Schoolid : ')
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent="\t")
    exit(0)

api = ondl.API(prefix=json_data['prefix'], schoolid=json_data['schoolid'])
user = api.login(id=json_data['id'], password=json_data['pw'])

def print_menu():
    print(r"""
███████╗██████╗ ███████╗    ███████╗██╗   ██╗ ██████╗  ██████╗ ██████╗ ██╗███╗   ██╗ ██████╗         
██╔════╝██╔══██╗██╔════╝    ██╔════╝██║   ██║██╔════╝ ██╔═══██╗██╔══██╗██║████╗  ██║██╔════╝       
█████╗  ██████╔╝███████╗    ███████╗██║   ██║██║  ███╗██║   ██║██████╔╝██║██╔██╗ ██║██║  ███╗     
██╔══╝  ██╔══██╗╚════██║    ╚════██║██║   ██║██║   ██║██║   ██║██╔══██╗██║██║╚██╗██║██║   ██║       
███████╗██████╔╝███████║    ███████║╚██████╔╝╚██████╔╝╚██████╔╝██║  ██║██║██║ ╚████║╚██████╔╝ 
╚══════╝╚═════╝ ╚══════╝    ╚══════╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝                                                                                                                                     
    """)
    print('v'+ version)
    print("1. Single download")
    print("2. Multiple download")
    print("4. Exit")
    menu = input("Selection: ")
    return int(menu)

def run():
    while 1:

        menu = print_menu()
        if menu == 1:
            LctrData = dict()
            url = input('URL : ')
            parse_url = parse_qsl(url)
            Lctr = api.readLctr(user, parse_url[0][1], parse_url[1][1], parse_url[2][1])
            api.download(Lctr.files, Lctr.Lctrtitle, Lctr.cntntsTyCode, Lctr.Classtitle)

        if menu == 2:
            LctrData = dict()
            url = input('URL : ')
            parse_url = parse_qsl(url)
            LctrList = api.readList(user, parse_url[0][1], parse_url[1][1], parse_url[2][1])
            print('Complete to analyse Lecture list ' + str(len(LctrList)))
            starts = int(input('Start range '))
            ends = int(input('End range '))

            for i in range(starts, ends + 1):
                Lctr = api.readLctr(user, parse_url[0][1], parse_url[1][1], LctrList[i - 1])
                api.download(Lctr.files, Lctr.Lctrtitle + '(' + str(i) + ')', Lctr.cntntsTyCode, Lctr.Classtitle)

            print('Done!')
        if menu == 4:
            exit(0)

run()