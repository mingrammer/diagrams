# Contribution Guide - How to Setup Environment

# WARNING - 19 Apr 2020 - The below creates an environment where you can successfully run the tests 

# However it still needs testing again; and also needs worked example on actually contributing 'value' and not putting noise back into the repository!

Whilst using Diagrams is easy and some folks will find setting up and extending Diagrams easy - for others with Python, Bash and Go dependancies it is harder...

So a worked guide to setting up a VM with linux so you can contribute to Diagrams.

Thanks: Thanks to ViktorOrda for assist on getting this to work.

This guide was written using ubuntu 18.04 on Azure. 

## VM
Easiest and cleanest way is to boot a new Linux VM on your cloud provide of choice. 
* 16 GB HDD is more than enough
* 2 GB Ram is more than enough 

## Required Software

To contribute to Diagrams you will need the required software (all installed from command prompt):

* Update apt (so you can find stuff)
```shell
    sudo apt update   
```

* Python - You want version 3 (Diagrams needs this)
```shell
	python --version
```
If this returns a 2.7.x type number you are going to have to check python 3 is installed; You need Python 3.6.x

```shell
	python3 --version
```
If Python3 does not return a suitable version you will need to install Python3.
```shell
    sudo apt-get install python3
```

Then to make sure the Diagrams autogen.sh script will work correctly we need to make the alias for 'python' to map to python3.
To make python3 the default run this:
```shell
 sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10


    NOT: sudo update-alternatives  --set python /usr/bin/python3.6
```
Or Google 'how to alias python3 to python' and similar to get into the whole aliasing topic. 



* pip (to make your life easier) - will probably report already installed. 
 ```shell
    sudo apt install python3-pip
```
* Git
 ```shell
    sudo apt install git
```
* Go 
    * Security warning (hence --classic) and hence why use VM
 ```shell   
    sudo snap install go --classic
```

* Black (used by autogen.sh)
 ```shell   
    pip3 install black
```

*NOW DISCONNECT from SSH and reconnect* (to reset your environment path otherwise Black won't work)

## Requirements as per Contributing page
* Round
```shell
    go get github.com/mingrammer/round
    sudo cp go/bin/round /bin
```

* Inkscape
 ```shell
    sudo apt install inkscape
```
* Convert
 ```shell
    pip install convert
``` 

## Grab the Diagrams Code
 ```shell
   git clone https://github.com/mingrammer/diagrams.git
``` 
## To Run the Autogen
 ```shell
   cd diagrams
    ./autogen.sh
``` 

# Actually Building the solution and installing diagrams; getting tests to pass

Whilst ./autogen.sh works the tests don't (because Diagrams isn't actually installed yet) and also as Diagrams isn't installed you can generate any pictures i.e. test your contribution
So some more things to install before you can run Diagrams. 

*Be careful here as you will create folders in the diagrams folder that you don't want to contribute back into the repository!*



```shell
    sudo apt-get install graphviz
    sudo pip install poetry
    sudo apt-get install python3-venv
    poetry build
    poetry install
```

Now from the diagrams folder run:
 ```shell
   python -m unittest tests/*.py -v
``` 
and all the tests should pass. 

 