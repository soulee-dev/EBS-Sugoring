import os
import re
import shutil
import requests
from tqdm import tqdm
from pytube import YouTube
from bs4 import BeautifulSoup as bs

s = requests.Session()

#로그인 요청 헤더 - UA 우회
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 Mobile Safari/537.36'
}

class Lctr:
    def __init__(self, atnlcNo, stepSn, lctreSn, cntntsTyCode, Classtitle, Lctrtitle, content, files=None):
        self.atnlcNo = atnlcNo
        self.stepSn = stepSn
        self.lctreSn = lctreSn
        self.cntntsTyCode = cntntsTyCode #001 EBS 자체 호스팅 영상 014 유튜브
        self.Classtitle = Classtitle
        self.Lctrtitle = Lctrtitle
        self.content = content
        self.files = files

class API:

    prefix = ''
    schoolid = ''
    SESSION = ""
    URL = ""

    def __init__(self, prefix, schoolid):
        self.prefix = prefix
        self.schoolid = schoolid
        self.URL = 'https://' + self.prefix  +'.ebssw.kr/' + '/'

    def login(self, id, password):

        #로그인 요청 페이로드
        LOGON = {
            'j_username': id,
            'j_password': password,
            'loginType': 'onlineClass',
            'hmpgId': self.schoolid,
            'c': 'LI'
        }

        with requests.Session() as S:     #with 사용시 __enter__ __exit__ 처리 해줘서 더 깔쌈함..
            response = S.post(self.URL + 'sso', data=LOGON, headers=HEADER)

            if not response.ok:
                raise Exception('Login failed ' + response.text)

            return S

    def mypage(self, user):
        response = user.post(self.URL + self.schoolid + '/hmpg/mypageLrnTabView.do?lrnType=LRN', headers=HEADER)
        soup = bs(response.text, 'html.parser')

        return soup.select('#record01 > div > ul > li')

    def readLctr(self, user, atnlcNo, stepSn, lctreSn):

        files = []
        URL = ''
        PARAMS = {
            'atnlcNo': atnlcNo,  # 파라미터 분석 필요..
            'stepSn': stepSn,
            'lctreSn': lctreSn,
            'sessSn': ''
        }

        response = user.get(self.URL + 'mypage/userlrn/userLrnView.do', params=PARAMS, headers=HEADER)
        soup = bs(response.text, 'html.parser')

        pattern = re.compile('loadCntnts?.*?;')
        regex = pattern.findall(response.text)

        pattern = re.compile('"(.*?)"')
        regex = pattern.findall(regex[len(regex) - 8])

        cntntsTyCode = regex[1]

        Classtitle = soup.select('#learn_header > div > strong')[0].text.strip()

        if cntntsTyCode == '001' or cntntsTyCode == '014' or cntntsTyCode == '015': #동영상
            URL = 'mypage/userlrn/userLrnMvpView.do'
        elif cntntsTyCode == '006': #문서
            URL = 'mypage/userlrn/userLrnDocView.do'
        elif cntntsTyCode == "005": #이미지
            URL = 'mypage/userlrn/userLrnImageView.do'
        elif cntntsTyCode == "012":#텍스트
            URL = 'mypage/userlrn/userLrnTextView.do'


        response = user.post(self.URL + URL, params=PARAMS, headers=HEADER)
        soup = bs(response.text, 'html.parser')

        Lctrtitle = soup.select('.content_tit')[0].text
        content = soup.select('#lctreCn')[0]['value']

        if cntntsTyCode == '001': #EBS 자체
            scripts = str(soup.select('script')[2])
            pattern = re.compile('https?.*?\.mp4')
            for i, v in enumerate(pattern.findall(scripts)):
                if i == 0:
                    files.append({'SD': v.replace('\\', '')})
                else:
                    files.append({'HD': v.replace('\\', '')})
                    break

        elif cntntsTyCode == '014': #유튜브
            files.append({'url': soup.select('#iframeYoutube')[0]['src']})

        elif cntntsTyCode == '006':
            pattern = re.compile("\'[^\']*\'")

            for i, v in enumerate(soup.select('.txt_violet > a')):
                for j, val in enumerate(pattern.findall(v['onclick'])):
                    if j == 1:
                        files[i]['fileSn'] = val.strip("'")
                        break
                    files.append({'atchFileId': val.strip("'")})

        return Lctr(atnlcNo=atnlcNo, stepSn=stepSn, lctreSn=lctreSn, cntntsTyCode=cntntsTyCode, Classtitle=Classtitle, Lctrtitle=Lctrtitle, content=content, files=files)

    def readList(self, user, atnlcNo, stepSn, lctreSn):

        LctrList = []

        PARAMS = {
            'atnlcNo': atnlcNo,  # 파라미터 분석 필요..
            'stepSn': stepSn,
            'lctreSn': lctreSn,
            'sessSn': ''
        }

        response = user.get(self.URL + 'mypage/userlrn/userLrnView.do', params=PARAMS, headers=HEADER)
        soup = bs(response.text, 'html.parser')

        pattern = re.compile('loadCntnts?.*?;')
        regex = pattern.findall(response.text)

        for i in range(8):
            regex.pop()

        for i, v in enumerate(regex):
            pattern = re.compile("'(.*?)'")
            regex = pattern.findall(v)
            LctrList.append(regex[0])

        return LctrList

    def download(self, files, title, cntntsTyCode, folder, resoultion='HD'):

        def progress_func(stream, chunk, bytes_remaining):  # tqdm 이용']
            with tqdm(total=stream.filesize) as pbar:
                pbar.update(stream.filesize - bytes_remaining)

        if cntntsTyCode == '001': #EBS 자체
            url = ''

            if resoultion == 'HD':
                url = files[1]['HD']
            elif resoultion == 'SD':
                url = files[0]['SD']

            with open(title + '.mp4', 'wb') as f:  # Binary Write 모드
                response = requests.get(url, stream=True)  # files 0은 SD 1은 HD

                fsize = response.headers.get('content-length')

                print('Downloading ' + title)

                with tqdm(total=int(fsize)) as pbar:
                    for data in response.iter_content(chunk_size=4096):
                        f.write(data)
                        pbar.update(len(data))

        elif cntntsTyCode == '014': #유튜브
            yt = YouTube(files[0]['url'], on_progress_callback=progress_func)
            yt_streams = yt.streams

            if resoultion == 'HD':
                my_stream = yt_streams.get_by_itag('137')
            elif resoultion == 'SD':
                my_stream = yt_streams.get_by_itag('136')

            print('Downloading ' + title)

            try:
                my_stream.download()
            except:
                my_stream = yt_streams.get_by_itag('18')
                my_stream.download()

            os.rename(my_stream.default_filename, title + '.mp4')

        else:
            print('Passing Lecture because this is not video type : ' + title)
            return 0

        if not os.path.isdir(folder):
            os.makedirs(folder)

        shutil.move(title + '.mp4', folder)





