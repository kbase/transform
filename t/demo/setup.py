#! /usr/bin/env python
from __future__ import print_function
import os
import sys
import shutil
import tarfile
import subprocess
from distutils.dir_util import mkpath
import stat

KBASE_DEPENDENCIES = ['kbase/user_and_job_state', 'kbase/workspace_deluxe',
                      'mlhenderson/handle_service', 'kbase/kbapi_common']
GITHUB_URL = 'https://github.com/'


def main():
    running_dir = os.getcwd()
    tve = TransformVirtualEnv(running_dir, 'venv', '../../')
    tve.download_demo_data()
    tve.print_instructions()


def touch(fname, times=None):
    '''Python implementation of the unix touch command. See os.utime for the
    format of the times argument. Reference:
    http://stackoverflow.com/questions/1158076/implement-touch-using-python
    '''

    with file(fname, 'a'):
        os.utime(fname, times)


class TransformVirtualEnv(object):

    def __init__(self, working_dir, venv_name, transform_repo,
                 keep_current_venv=False):
        self.working_dir = os.path.abspath(working_dir)
        self.venv_dir = os.path.join(self.working_dir, venv_name)

        if not keep_current_venv:
            try:
                shutil.rmtree(self.venv_dir)
            except:
                pass

            # create a virtualenv under the services directory
            subprocess.call(["virtualenv", "--python", "python2.7",
                             "--system-site-packages", self.venv_dir])
            subprocess.call([os.path.join(self.venv_dir, "bin/pip"),
                             "install", "pip", "ftputil", "requests",
                             "httplib2", "requests_toolbelt", "gitpython",
                             "filemagic", "blessings", "python-dateutil",
                             "simplejson", "configobj"])

        sys.path.append(os.path.join(self.venv_dir,
                                     "lib/python2.7/site-packages/"))
        global git
        global requests
        # these imports are actually used since they're made global by the
        # above lines; the pep8 checker is just stupid in this case
        import git  # @UnusedImport
        import requests  # @UnusedImport
        if not keep_current_venv:
            self._build_dependencies(transform_repo)

    # not sure if this should be called independently from __init__, prob not
    def _build_dependencies(self, transform_dir):
        target_dir = os.path.join(self.venv_dir,
                                  'lib/python2.7/site-packages/biokbase')
        mkpath(target_dir)
        touch(os.path.join(target_dir, '__init__.py'))
        shutil.copytree(
            os.path.join(transform_dir, "lib/biokbase/Transform"),
            os.path.join(self.venv_dir,
                         "lib/python2.7/site-packages/biokbase/Transform"))

        print("Pulling git dependencies")
        for dep in KBASE_DEPENDENCIES:
            print("Checking out " + GITHUB_URL + dep)
            repo = os.path.split(dep)[1]
            gitdir = os.path.join(self.working_dir, repo)
            git.Git().clone(GITHUB_URL + dep, gitdir)
            self._copy_deps(gitdir)
            shutil.rmtree(os.path.join(gitdir))

        scripts_dir = os.path.join(transform_dir, "plugins/scripts/")
        bin_dir = os.path.join(self.venv_dir, "bin/")
        for root, _, files in os.walk(scripts_dir):
            for file_ in files:
                filepath = os.path.join(root, file_)
                print("copy from {0} {1}".format(filepath, bin_dir))
                shutil.copy(filepath, bin_dir)
                self._make_executable_for_all(os.path.join(bin_dir, file_))
                self._make_wrapper(bin_dir, file_)

    def _copy_deps(self, gitdir):
        libdir = os.path.join(gitdir, 'lib/biokbase')
        for item in os.listdir(libdir):
            src = os.path.join(libdir, item)
            target = os.path.join(self.venv_dir,
                                  'lib/python2.7/site-packages/biokbase', item)
            if os.path.isdir(src):
                shutil.copytree(src, target)
            elif os.path.isfile(src) and src != '__init__.py':
                shutil.copy(src, target)
            # else skip

    def _make_wrapper(self, dir_, file_):
        wrapperfile = os.path.join(dir_, os.path.splitext(file_)[0])
        with open(wrapperfile, 'w') as wrapper:
            wrapper.write('#!/usr/bin/env sh\n')
            wrapper.write(os.path.join(dir_, file_) + ' "$@"\n')
        self._make_executable_for_all(wrapperfile)

    def _make_executable_for_all(self, file_):
        st = os.stat(file_)
        os.chmod(file_, st.st_mode | stat.S_IXUSR | stat.S_IXGRP |
                 stat.S_IXOTH)

    def download_demo_data(self):
        if not os.path.isdir(os.path.join(self.working_dir, "data")):
            print("Downloading demo data, data.tar.bz2")

            data = requests.get("http://140.221.67.242/data/data.tar.bz2",
                                stream=True)
            data_file = os.path.join(self.working_dir, "data.tar.bz2")
            with open(data_file, 'wb') as f:
                for chunk in data.iter_content(10 * 2**20):
                    f.write(chunk)

            print("Extracting demo data")

            with tarfile.open(data_file, 'r') as tarDataFile:
                tarDataFile.extractall()
            os.remove(data_file)

    def print_instructions(self):
        print("Make sure to use kbase-login or export KB_AUTH_TOKEN")
        print("Run the upload client driver with " +
              "venv/bin/python bin/upload_client.py --demo")
        print("Run the upload developer script driver with venv/bin/python " +
              "bin/upload_script_test.py --demo")

    def activate_for_current_py_process(self):
        activate_this = os.path.join(self.venv_dir, 'bin/activate_this.py')
        execfile(activate_this, dict(__file__=activate_this))

    def get_scripts_path(self):
        return os.path.join(self.venv_dir, 'bin')

if __name__ == '__main__':
    main()
