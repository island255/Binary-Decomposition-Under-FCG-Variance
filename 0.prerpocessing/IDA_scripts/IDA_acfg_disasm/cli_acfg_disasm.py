#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##############################################################################
#                                                                            #
#  Code for the USENIX Security '22 paper:                                   #
#  How Machine Learning Is Solving the Binary Function Similarity Problem.   #
#                                                                            #
#  MIT License                                                               #
#                                                                            #
#  Copyright (c) 2019-2022 Cisco Talos                                       #
#                                                                            #
#  Permission is hereby granted, free of charge, to any person obtaining     #
#  a copy of this software and associated documentation files (the           #
#  "Software"), to deal in the Software without restriction, including       #
#  without limitation the rights to use, copy, modify, merge, publish,       #
#  distribute, sublicense, and/or sell copies of the Software, and to        #
#  permit persons to whom the Software is furnished to do so, subject to     #
#  the following conditions:                                                 #
#                                                                            #
#  The above copyright notice and this permission notice shall be            #
#  included in all copies or substantial portions of the Software.           #
#                                                                            #
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,           #
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF        #
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                     #
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE    #
#  LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION    #
#  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION     #
#  WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.           #
#                                                                            #
#  cli_acfg_disasm.py - Call IDA_acfg_disasm.py IDA script.                  #
#                                                                            #
##############################################################################

import click
import json
import subprocess
import time

import os
from tqdm import tqdm
from multiprocessing import Pool
import ntpath

from os import getenv
from os.path import abspath
from os.path import dirname
from os.path import isfile
from os.path import join

IDA_PATH = getenv("IDA_PATH", "/data1/jiaang/tool/idapro-7.3/idat64")
IDA_PLUGIN = join(dirname(abspath(__file__)), 'IDA_acfg_disasm.py')
REPO_PATH = dirname(dirname(dirname(abspath(__file__))))
LOG_PATH = "acfg_disasm_log.txt"


def run_ida_get_acfg_disam(cmd):
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()


@click.command()
@click.option('-j', '--json-path', required=True,
              help='JSON file with selected functions.')
@click.option('-o', '--output-dir', required=True,
              help='Output directory.')
def main(json_path, output_dir):
    """Call IDA_acfg_disasm.py IDA script."""
    try:
        if not isfile(IDA_PATH):
            print("[!] Error: IDA_PATH:{} not valid".format(IDA_PATH))
            print("Use 'export IDA_PATH=/full/path/to/idat64'")
            return

        print("[D] JSON path: {}".format(json_path))
        print("[D] Output directory: {}".format(output_dir))

        if not isfile(json_path):
            print("[!] Error: {} does not exist".format(json_path))
            return

        with open(json_path) as f_in:
            jj = json.load(f_in)

            cmd_list = []
            success_cnt, error_cnt = 0, 0
            start_time = time.time()
            for idb_rel_path in jj.keys():
                # print("\n[D] Processing: {}".format(idb_rel_path))

                # Convert the relative path into a full path
                idb_path = join(REPO_PATH, idb_rel_path)
                # print("[D] IDB full path: {}".format(idb_path))

                if not isfile(idb_path):
                    print("[!] Error: {} does not exist".format(idb_path))
                    continue

                cmd = [IDA_PATH,
                       '-A',
                       '-L{}'.format(LOG_PATH),
                       '-S{}'.format(IDA_PLUGIN),
                       '-Oacfg_disasm:{}:{}:{}'.format(
                           json_path,
                           idb_rel_path,
                           output_dir),
                       idb_path]

                out_name = ntpath.basename(idb_path.replace(".i64", "_acfg_disasm.json"))
                ouptut_file_path = os.path.join(output_dir, out_name)
                if os.path.exists(ouptut_file_path):
                    continue

                cmd_list.append(cmd)

                # print("[D] cmd: {}".format(cmd))

                # proc = subprocess.Popen(
                #     cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # stdout, stderr = proc.communicate()

                # if proc.returncode == 0:
                #     print("[D] {}: success".format(idb_path))
                #     success_cnt += 1
                # else:
                #     print("[!] Error in {} (returncode={})".format(
                #         idb_path, proc.returncode))
                #     error_cnt += 1

            process_num = 1
            p = Pool(int(process_num))
            with tqdm(total=len(cmd_list)) as pbar:
                for i, res in tqdm(enumerate(p.imap_unordered(run_ida_get_acfg_disam, cmd_list))):
                    pbar.update()
            p.close()
            p.join()

            end_time = time.time()
            print("[D] Elapsed time: {}".format(end_time - start_time))
            with open(LOG_PATH, "a+") as f_out:
                f_out.write("elapsed_time: {}\n".format(end_time - start_time))

            print("\n# IDBs correctly processed: {}".format(success_cnt))
            print("# IDBs error: {}".format(error_cnt))

    except Exception as e:
        print("[!] Exception in cli_acfg_disasm\n{}".format(e))


if __name__ == '__main__':
    main()
