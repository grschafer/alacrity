git submodule init

git submodule update

install tarrasque and skadi to virtualenv

run\_all will run the scripts specified inside it on all the .dem files in the directory/tree passed on command line

to run an individual script on multiple files use:

    find /path/to/demo/dir/ -type f | xargs -I {} python script_name.py {}
