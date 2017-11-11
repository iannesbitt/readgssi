function data=readgssi(name)


fid=fopen(name);
rh.tag=fread(fid,1,'ushort');
rh.data=fread(fid,1,'ushort');
rh.nsamp=fread(fid,1,'ushort');
rh.bits=fread(fid,1,'ushort');

rh.zero=fread(fid,1,'short');

rh.sps=fread(fid,1,'float');
rh.spm=fread(fid,1,'float');
rh.mpm=fread(fid,1,'float');
rh.position=fread(fid,1,'float');
rh.range=fread(fid,1,'float');

rh.npass=fread(fid,1,'ushort');

Create.sec2=fread(fid,1,'ubit5'); 
Create.min=fread(fid,1,'ubit6'); 
Create.hour=fread(fid,1,'ubit5');
Create.day=fread(fid,1,'ubit5'); 
Create.month=fread(fid,1,'ubit4'); 
Create.year=fread(fid,1,'ubit7'); 

Modify.sec2=fread(fid,1,'ubit5'); 
Modify.min=fread(fid,1,'ubit6'); 
Modify.hour=fread(fid,1,'ubit5');
Modify.day=fread(fid,1,'ubit5'); 
Modify.month=fread(fid,1,'ubit4'); 
Modify.year=fread(fid,1,'ubit7'); 

rh.rgain=fread(fid,1,'ushort');
rh.nrgain=fread(fid,1,'ushort');
rh.text=fread(fid,1,'ushort');
rh.ntext=fread(fid,1,'ushort');
rh.proc=fread(fid,1,'ushort');
rh.nproc=fread(fid,1,'ushort');
rh.nchan=fread(fid,1,'ushort');

rh.epsr=fread(fid,1,'float');
rh.top=fread(fid,1,'float');
rh.depth=fread(fid,1,'float');

reserved=fread(fid,31,'char');
rh.dtype=fread(fid,1,'char');
rh.antname=fread(fid,14,'char');
rh.chanmask=fread(fid,1,'ushort');
rh.name=fread(fid,12,'char');
rh.chksum=fread(fid,1,'ushort');
%rh.var=setstr(fread(fid,896,'char'));
rh.Gain=fread(fid,1,'ushort');
rh.Gainpoints=fread(fid,rh.Gain,'float');
rh.comments=setstr(fread(fid,rh.ntext,'char'));
rh.proccessing=fread(fid,rh.nproc,'char');

fseek(fid,0,'bof');
fseek(fid,1024,'bof');

d=fread(fid,[rh.nsamp inf],'ushort');
d(1,:)=d(3,:);
d(2,:)=d(3,:);
d=d+rh.zero;

data.head=rh;
data.samp=d;
fclose(fid);
