'''
Created on Jan 30, 2015

@author: gaprice@lbl.gov
'''
from __future__ import print_function
import os
import inspect
from biokbase.Transform import script_utils
from biokbase.Transform.handler_utils import PlugIns
from biokbase.AbstractHandle.Client import AbstractHandle
from bzrlib.config import ConfigObj
import json
from biokbase.workspace.client import Workspace
import random
import sys
import subprocess
from deep_eq import deep_eq

# TODO run this with makefile
# TODO more test cases

KB_TOKEN = 'KB_AUTH_TOKEN'
TEST_CFG_FILE = 'test.cfg'

FILE_LOC = os.path.split(__file__)[0]

sys.path.append(os.path.join(FILE_LOC, '../'))  # to import demo/setup
# this import is both resolved and used
from demo.setup import TransformVirtualEnv  # @UnresolvedImport @UnusedImport

TRANSFORM_LOC = os.path.join(FILE_LOC, '../../')
# maybe this should be configurable...?
PLUGIN_CFG_LOC = os.path.join(TRANSFORM_LOC, 'plugins/configs')


class Test_Scripts(object):

    @classmethod
    def setup_class(cls):
        cls.token = os.environ.get(KB_TOKEN)
        if not cls.token:
            raise ValueError('No token found in environment variable ' +
                             KB_TOKEN)
        cls.plugins_cfg = PlugIns(PLUGIN_CFG_LOC)
        cfg = ConfigObj(TEST_CFG_FILE)
        for url in ['ws_url', 'shock_url', 'handle_url', 'ujs_url']:
            setattr(cls, url, cfg.get(url))
        tve = TransformVirtualEnv(FILE_LOC, 'venv', TRANSFORM_LOC,
                                  keep_current_venv=False)
        tve.activate_for_current_py_process()
        cls.staged = {}
        cls.stage_data()

    @classmethod
    def stage_data(cls):
        cls.stage_assy_file()
        cls.stage_empty_data()

    @classmethod
    def stage_empty_data(cls):
        this_function_name = sys._getframe().f_code.co_name
        src_obj_name = 'empty'
        src_type = 'Empty.AType'

        src_ws = cls.create_random_workspace(this_function_name)
        ws = Workspace(cls.ws_url, token=cls.token)
        objdata = ws.save_objects(
            {'workspace': src_ws,
             'objects': [{'name': src_obj_name,
                          'type': src_type,
                          'data': {}}]
             })[0]
        cls.staged['empty'] = {'obj_info': objdata}

    @classmethod
    def stage_assy_file(cls):
        this_function_name = sys._getframe().f_code.co_name
        src_obj_name = 'test_assy_file'
        src_type = 'KBaseFile.AssemblyFile'

        test_file = os.path.join(FILE_LOC, 'test_files/sample.fa')
        node_id, handle = cls.upload_file_to_shock_and_get_handle(test_file)

        test_json = os.path.join(FILE_LOC, 'test_files/AssemblyFile.json')
        with open(test_json) as assyjsonfile:
            assyjson = json.loads(assyjsonfile.read())
        assyjson['assembly_file']['file']['url'] = cls.shock_url
        assyjson['assembly_file']['file']['id'] = node_id
        assyjson['assembly_file']['file']['hid'] = handle

        src_ws = cls.create_random_workspace(this_function_name)
        ws = Workspace(cls.ws_url, token=cls.token)
        objdata = ws.save_objects(
            {'workspace': src_ws,
             'objects': [{'name': src_obj_name,
                          'type': src_type,
                          'data': assyjson}]
             })[0]
        ref = str(objdata[6]) + '/' + str(objdata[0]) + '/' + str(objdata[4])
        cls.staged['assy_file'] = {'obj_info': objdata,
                                   'node': node_id,
                                   'ref': ref}

    @classmethod
    def upload_file_to_shock_and_get_handle(cls, test_file):
        node_id = script_utils.upload_file_to_shock(
            shock_service_url=cls.shock_url,
            filePath=test_file,
            ssl_verify=False,
            token=cls.token)['id']

        handle = AbstractHandle(cls.handle_url, token=cls.token)
        handle_id = handle.persist_handle({'id': node_id,
                                           'type': 'shock',
                                           'url': cls.shock_url
                                           })
        return node_id, handle_id

    @classmethod
    def create_random_workspace(cls, prefix):
        ws = Workspace(cls.ws_url, token=cls.token)
        ws_name = prefix + '_' + str(random.random())[2:]
        wsinfo = ws.create_workspace({'workspace': ws_name})
        return wsinfo[1]

    @classmethod
    def run_convert_taskrunner(cls, args):
        input_args = cls.plugins_cfg.get_handler_args("convert", args)
        command_list = ['trns_convert_taskrunner.py']

        for k in input_args:
            command_list.append("--{0}".format(k))
            command_list.append("{0}".format(input_args[k]))

        task = subprocess.Popen(command_list, stderr=subprocess.PIPE)
        so, se = task.communicate()
        return so, se, task.returncode

    def test_assyfile_to_cs_basic_ops(self):
        this_function_name = sys._getframe().f_code.co_name
        staged = self.staged['assy_file']

        dest_ws = self.create_random_workspace(this_function_name)
        dest_obj_name = 'foo2'

        args = {'source_kbase_type': staged['obj_info'][2].split('-')[0],
                'destination_kbase_type': 'KBaseGenomes.ContigSet',
                'source_workspace_name': staged['obj_info'][7],
                'destination_workspace_name': dest_ws,
                'source_object_name': staged['obj_info'][1],
                'destination_object_name': dest_obj_name,
                'workspace_service_url': self.ws_url,
                'ujs_service_url': self.ujs_url,
                'working_directory': dest_ws}

        stdo, stde, code = self.run_convert_taskrunner(args)
        if stdo:
            raise TestException('Got unexpected data in standard out:\n' +
                                stdo)
        if 'ERROR' in stde:
            raise TestException('Error reported in stderr:\n' + stde)
        if 'INFO - Conversion completed.' not in stde:
            raise TestException('Script did not report as completed:\n' + stde)
        if code != 0:
            raise TestException('Got non zero return code from script:' +
                                str(code))

        ws = Workspace(self.ws_url, token=self.token)
        newobj = ws.get_objects([{'workspace': dest_ws,
                                  'name': dest_obj_name}])[0]
        prov = newobj['provenance'][0]
        ref = staged['ref']
        assert prov['input_ws_objects'] == [ref]
        assert prov['resolved_ws_objects'] == [ref]
        assert prov['script'] ==\
            'trns_transform_KBaseFile_AssemblyFile_to_KBaseGenomes_ContigSet'
        assert prov['script_ver'] == '0.0.1'

        with open(os.path.join(FILE_LOC, 'test_files/ContigSetOut.json')) as f:
            expected = json.loads(f.read())
        expected['fasta_ref'] = staged['node']
        deep_eq(expected, newobj['data'], _assert=True)

    def test_assyfile_to_cs_fail_ws_error(self):
        this_function_name = sys._getframe().f_code.co_name
        staged = self.staged['assy_file']

        src_ws = staged['obj_info'][7]

        args = {'source_kbase_type': staged['obj_info'][2].split('-')[0],
                'destination_kbase_type': 'KBaseGenomes.ContigSet',
                'source_workspace_name': src_ws + 'thisllbreakthings',
                'destination_workspace_name': 'no-such-ws%$^%',
                'source_object_name': staged['obj_info'][1],
                'destination_object_name': 'foo2',
                'workspace_service_url': self.ws_url,
                'ujs_service_url': self.ujs_url,
                'working_directory': this_function_name}

        expect = 'Object test_assy_file cannot be accessed: No workspace ' +\
            'with name stage_assy_file'
        self.fail_convert(args, expect)

    def test_assyfile_to_cs_fail_ws_type(self):
        this_function_name = sys._getframe().f_code.co_name
        staged = self.staged['empty']

        args = {'source_kbase_type': 'KBaseFile.AssemblyFile',
                'destination_kbase_type': 'KBaseGenomes.ContigSet',
                'source_workspace_name': staged['obj_info'][7],
                'destination_workspace_name': 'non-existent-workspace@#$',
                'source_object_name': staged['obj_info'][1],
                'destination_object_name': 'foo2',
                'workspace_service_url': self.ws_url,
                'ujs_service_url': self.ujs_url,
                'working_directory': this_function_name}

        expect = 'This method only works on the KBaseFile.AssemblyFile type'
        self.fail_convert(args, expect)

    def fail_convert(self, args, expected_error):
        stdo, stde, code = self.run_convert_taskrunner(args)
        if stdo:
            raise TestException('Got unexpected data in standard out:\n' +
                                stdo)
        if expected_error not in stde:
            raise TestException('Did not get expected error in stderr:\n' +
                                stde)
        if code != 1:
            raise TestException('Got unexpected return code from script:' +
                                str(code))


class TestException(Exception):
    pass


def main():
    # use nosetests to run these tests, this is a hack to get them to run
    # while testing the tests
    Test_Scripts.setup_class()
    ts = Test_Scripts()
    methods = inspect.getmembers(ts, predicate=inspect.ismethod)
    for meth in methods:
        if meth[0].startswith('test_'):
            print("\nRunning " + meth[0])
            meth[1]()


if __name__ == '__main__':
    main()
