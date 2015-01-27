import os
import os.path
import sys
import shutil

running_dir = os.getcwd()

virtualenv_dir = os.path.join(running_dir,"venv")

try:
    shutil.rmtree(virtualenv_dir)
except:
    pass

# create a virtualenv under the services directory
import subprocess
subprocess.call(["virtualenv","--python","python2.7","--system-site-packages",virtualenv_dir])
subprocess.call([os.path.join(virtualenv_dir, "bin/pip"), "install","pip","ftputil","requests","httplib2","requests_toolbelt","gitpython","filemagic","blessings","python-dateutil","simplejson"])

sys.path.append("./venv/lib/python2.7/site-packages/")

print "Checking out user_and_job_state,workspace_deluxe,handle_service client code"

import git
git.Git().clone("https://github.com/kbase/user_and_job_state")
git.Git().clone("https://github.com/kbase/workspace_deluxe")
git.Git().clone("https://github.com/mlhenderson/handle_service")
git.Git().clone("https://github.com/kbase/kbapi_common")

print "Copying client code to virtualenv"

# copy client code into the virtualenv directory
shutil.copytree(os.path.join(running_dir,"user_and_job_state/lib/biokbase"), os.path.join(virtualenv_dir, "lib/python2.7/site-packages/biokbase"))
shutil.copytree(os.path.join(running_dir,"workspace_deluxe/lib/biokbase/workspace"), os.path.join(virtualenv_dir, "lib/python2.7/site-packages/biokbase/workspace"))
shutil.copytree(os.path.join(running_dir,"handle_service/lib/biokbase/AbstractHandle"), os.path.join(virtualenv_dir, "lib/python2.7/site-packages/biokbase/AbstractHandle"))
shutil.copytree(os.path.join(running_dir,"../../lib/biokbase/Transform"), os.path.join(virtualenv_dir, "lib/python2.7/site-packages/biokbase/Transform"))

shutil.copy(os.path.join(running_dir,"kbapi_common/lib/biokbase/log.py"), os.path.join(virtualenv_dir, "lib/python2.7/site-packages/biokbase/"))


scripts = list()

for root, directories, files in os.walk(os.path.join(running_dir, "../../plugins/scripts/")):
    for file in files:
        print "copy from {0} {1}".format(os.path.join(root, file), os.path.join(virtualenv_dir,"bin/"))
        shutil.copy(os.path.join(root, file), os.path.join(virtualenv_dir,"bin/"))

print "Cleaning up checked out repos"

shutil.rmtree(os.path.join(running_dir,"user_and_job_state"))
shutil.rmtree(os.path.join(running_dir,"workspace_deluxe"))
shutil.rmtree(os.path.join(running_dir,"handle_service"))
shutil.rmtree(os.path.join(running_dir,"kbapi_common"))

if not os.path.isdir(os.path.join(running_dir, "data")):
    print "Downloading demo data, data.tar.bz2"

    import requests
    data = requests.get("http://140.221.67.242/data/data.tar.bz2", stream=True)
    with open(os.path.join(running_dir, "data.tar.bz2"), 'wb') as f:
        for chunk in data.iter_content(10 * 2**20):
            f.write(chunk)

    print "Extracting demo data"
    import tarfile
    with tarfile.open(os.path.join(running_dir, "data.tar.bz2"), 'r') as tarDataFile:
        tarDataFile.extractall()
    os.remove(os.path.join(running_dir, "data.tar.bz2"))

print "Make sure to use kbase-login or export KB_AUTH_TOKEN"
print "Run the upload client driver with venv/bin/python bin/upload_client.py --demo"
print "Run the upload developer script driver with venv/bin/python bin/upload_script_test.py --demo"

