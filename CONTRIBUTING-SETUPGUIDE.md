# Contribution Guide - How to Setup Environment

# WARNING - 18 Apr 2020 - THIS DOES NOT WORK YET!

Whilst using Diagrams is easy and some folks will find setting up and extending Diagrams easy - for others with Python, Bash and Go dependancies it is harder...

So a worked guide to setting up a VM with linux so you can contribute to Diagrams.

Disclosure: This was written using ubuntu 18.04 on Azure. 

## VM
Easiest and cleanest way is to boot a new Linux VM on your cloud provide of choice. 
* 16 GB HDD is more than enough
* 2 GB Ram is more than enough 

## Required Software

To contribute to Diagrams you will need the required software (all installed from command prompt):

* Python 2.7.x (comes pre-installed)

* pip (to make your life easier)
 ```shell
    sudo apt update
    sudo apt install python-pip
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
## To Run the Build
 ```shell
   cd diagrams
    ./autogen.sh
``` 

# Known Issues
When trying to run the build - which is needed to be able to be done before being able to contribute - autogen.sh causes:

```shell
....../diagrams$ ./autogen.sh
converting the svg to png using inkscape for provider 'onprem'
Traceback (most recent call last):
  File "/usr/lib/python2.7/runpy.py", line 163, in _run_module_as_main
    mod_name, _Error)
  File "/usr/lib/python2.7/runpy.py", line 102, in _get_module_details
    loader = get_loader(mod_name)
  File "/usr/lib/python2.7/pkgutil.py", line 462, in get_loader
    return find_loader(fullname)
  File "/usr/lib/python2.7/pkgutil.py", line 472, in find_loader
    for importer in iter_importers(fullname):
  File "/usr/lib/python2.7/pkgutil.py", line 428, in iter_importers
    __import__(pkg)
  File "scripts/__init__.py", line 7
    def app_root_dir(pvd: str) -> str:
                        ^
SyntaxError: invalid syntax
```
Hence we need to understand the dependancy which is missing to be able to contribute

## Comment
autogen.sh 
* is using bash which is installed
* The 'app_root_dir="diagrams"' does run 
* The checks for round, inkscape and convert all pass

But its failing as per error message above - which is beyond by Google-foo... (Or my Python knowledge which is not the greatest :-) 

# TO DO
* Add how to run modified code locally 