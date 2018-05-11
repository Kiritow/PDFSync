# PDF Sync Manager
# Created by Kiritow.

import platform
import os
from hashlib import md5
from ftplib import FTP

def ScanPDF(root_dir):
    lst=[]
    for parent,dirs,files in os.walk(root_dir):
        for file in files:
            if(file.endswith(".pdf")):
                lst.append([file,os.path.join(parent,file)])
    return lst

def GetMD5(filename):
    f=open(filename,'rb')
    h=md5()
    while True:
        b=f.read(4096)
        if not b:
            break
        h.update(b)
    f.close()
    return h.hexdigest()

def CheckPDF(lst):
    clst=[]
    flst=[]
    for pr in lst:
        m=GetMD5(pr[1])
        if(m in clst):
            print('md5 same: ' + pr[0] + '. Skipped.')
        else:
            clst.append(m)
            flst.append([pr[0],pr[1],m])
    return flst

def SyncPDF(uinfo,lst):
    mbcalc=lambda x:round(x/1024/1024,2)

    ftp=FTP(uinfo[0])
    ftp.encoding='UTF-8'
    ftp.login(uinfo[1],uinfo[2])

    ftp.cwd('/md5')
    remote_track_list=ftp.nlst()

    to_upload_list=[]
    to_upload_byte=0
    tmpid=0
    for name,addr,check in lst:
        tmpid=tmpid+1
        if(check not in remote_track_list):
            print('[' + str(tmpid) + '][Untracked] ' + name)
            to_upload_list.append([name,addr,check])
            to_upload_byte+=os.path.getsize(addr)
        else:
            print('[' + str(tmpid) + '][Synced] ' + name)

    to_upload_cnt=len(to_upload_list)
    if(to_upload_cnt<1):
        print('Nothing to upload.')
        return

    print('Totoally ' + str(to_upload_cnt) + ' files need to upload. ' 
        + 'Need to upload: ' + str(mbcalc(to_upload_byte)) + 'MB')
    choice=input('Are you sure to upload? (Y/N): ')
    if(choice!='Y'):
        print('Aborted.')
        return

    ftp.cwd('/')
    remote_filename_list=ftp.nlst()

    uploaded_byte=0
    for i in range(to_upload_cnt):
        print('[' + str(i+1) + '/' + str(to_upload_cnt) + '][Uploading] ' 
            + to_upload_list[i][0] + '...')
        
        # Adjust filename
        remote_filename=to_upload_list[i][0]
        while(remote_filename in remote_filename_list):
            remote_filename=remote_filename.replace(".pdf","_.pdf",1)
        
        # Upload
        with open(to_upload_list[i][1],'rb') as fp:
            file_byte=os.path.getsize(to_upload_list[i][1])
            print('file size: ' + str(mbcalc(file_byte)) + 'MB')
            ftp.storbinary('STOR '+remote_filename,fp)
            uploaded_byte+=file_byte
            print(str(mbcalc(uploaded_byte)) + 'MB uploaded. ('
                    + str(round(uploaded_byte/to_upload_byte*100,2)) + '%)')

            # MD5 file content must be utf-8
            with open(to_upload_list[i][2],'w',encoding='utf-8') as cf:
                cf.write(remote_filename)
            with open(to_upload_list[i][2],'rb') as cf:
                ftp.storbinary('STOR /md5/'+to_upload_list[i][2],cf)
            print('Check file ' + to_upload_list[i][2] + ' updated.')
            os.remove(to_upload_list[i][2])

def FetchInfo():
    svaddr=input('Server Addr:')
    uname=input('FTP Username:')
    upass=input('FTP Password:')
    return (svaddr,uname,upass)

# Main Program
print("""PDF Sync Manager
Author: Kiritow""")
search_dir=input('Enter root directory to search :')
print ('Scanning...')
tlst=ScanPDF(search_dir)
clst=CheckPDF(tlst)
print ('[Scan Result] ' + str(len(tlst)) + ' PDF found. ' + str(len(clst)) + ' unique PDF.')
print ('Syncing...')
uinfo=FetchInfo()
SyncPDF(uinfo,clst)
