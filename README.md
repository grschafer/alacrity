git submodule init

git submodule update

install tarrasque and skadi to virtualenv

run individual scripts (from the repo top-level directory) as follows:

    * python -m alacrity.parsers.script_name

run_all.py will run the scripts specified inside it on all the .dem files in the directory/tree passed on command line

to run an individual script on multiple files use:

    find /path/to/demo/dir/ -type f | xargs -I {} python script_name.py {}
