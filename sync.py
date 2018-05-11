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
            print('md5 same: ' + pr[0])
        else:
            clst.append(m)
            flst.append([pr[0],pr[1],m])
    return flst

def SyncPDF(uinfo,lst):
    ftp=FTP(uinfo[0])
    ftp.encoding='UTF-8'
    ftp.login(uinfo[1],uinfo[2])
    ftp.cwd('/md5')
    mlst=ftp.nlst()
    tlst=[]
    upsz=0
    tmpid=0
    for name,addr,check in lst:
        tmpid=tmpid+1
        if(check not in mlst):
            print('[' + str(tmpid) + '][Untracked] ' + name)
            tlst.append([name,addr,check])
            upsz+=os.path.getsize(addr)
        else:
            print('[' + str(tmpid) + '][Synced] ' + name)

    lsz=len(tlst)
    if(lsz<1):
        print('Nothing to upload.')
        return

    print("Totoally " + str(lsz) + " files need to upload. Need to upload: " + str(round(upsz/1024/1024,2)) + 'MB')
    choice=input('Are you sure to upload? (Y/N): ')
    if(choice!='Y'):
        print('Aborted.')
        return

    ftp.cwd('/')
    fnlst=ftp.nlst()

    donesz=0
    for i in range(lsz):
        print('[' + str(i+1) + '/' + str(lsz) + '][Uploading] ' + tlst[i][0])
        remote_filename=tlst[i][0]
        while(remote_filename in fnlst):
            remote_filename=remote_filename.replace(".pdf","_.pdf",1)
        with open(tlst[i][1],'rb') as fp:
            file_size=round(os.path.getsize(tlst[i][1])/1024/1024,2)
            donesz+=os.path.getsize(tlst[i][1])
            print('file size: ' + str(file_size) + 'MB')
            ftp.storbinary('STOR '+remote_filename,fp)
            print(str(round(donesz/1024/1024,2)) 
                    + "MB uploaded. ("
                    + str(round(donesz/upsz*100,2))
                    + '%)' )

            # MD5 file content must be utf-8
            with open(tlst[i][2],'w',encoding='utf-8') as cf:
                cf.write(remote_filename)
            with open(tlst[i][2],'rb') as cf:
                ftp.storbinary('STOR /md5/'+tlst[i][2],cf)
            print('Check file ' + tlst[i][2] + ' updated.')
            os.remove(tlst[i][2])

def FetchInfo():
    svaddr=input('Server Addr:')
    uname=input('FTP Username:')
    upass=input('FTP Password:')
    return (svaddr,uname,upass)

# Main Program
print("""PDF Sync Manager
Author: Kiritow""")
search_dir=input('Where should we start? :')
print ('Scanning...')
cl=CheckPDF(ScanPDF(search_dir))
print ('Syncing...')
uinfo=FetchInfo()
SyncPDF(uinfo,cl)

