git submodule init

git submodule update

install tarrasque and skadi to virtualenv

run scripts (from the repo top-level directory) with one of the following

    * python -m alacrity.parsers.script\_name
    * python script\_name.py

run\_all.py will run the scripts specified inside it on all the .dem files in the directory/tree passed on command line

to run an individual script on multiple files use:

    find /path/to/demo/dir/ -type f | xargs -I {} python script\_name.py {}
