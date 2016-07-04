#!/usr/bin/python
# coding: utf-8
'''
Create a job from a given config file
'''
from __future__ import print_function
import os
from os import walk
from os.path import abspath
from os.path import basename
from os.path import dirname
from os.path import join
import sys
import subprocess

from configparser import SafeConfigParser
from tqdm import tqdm


def generate_DAGman_job(argv):
    # store location of this file for relative file access of template files
    base_path = dirname(abspath(__file__))
    config = SafeConfigParser()
    try:
        config.read(argv[0])
    except:
        print('Use `./create_dagman_job <config-file>`')

    job_name = config.get('job', 'job_name')
    particle_types = config.get('data', 'particle_types').split(',')
    systematics = config.get('data', 'systematics')

    ending = config.get('data', 'file_ending')

    # ####################
    # ## dagman.config ###
    # ####################
    max_jobs = config.get('job', 'max_jobs')
    max_jobs_per_interval = config.get('job', 'max_jobs_per_interval')
    interval_length = config.get('job', 'interval_length')

    # #################
    # ## onejob.sub ###
    # #################
    environment = config.get('process', 'environment')
    executable = config.get('process', 'executable')
    # generate list of arguments
    # load arguments and values from config file, while converting it to
    # dagman argument friendly options a la '--argument $(value)'
    arguments = ['--{} $({})'.format(arg, arg) for arg in config['settings'].keys()]

    exec_ending = executable.split('.')[-1]
    program_dict = {'py': 'python',
                    'sh': 'bash'}
    arguments.insert(0, executable)
    try:
        program = program_dict[exec_ending]
    except:
        print('Please provide a program to execute {}'.format(executable))
        program = raw_input('program (path if not in PATH): ')
    arguments.insert(0, program)

    # ##################
    # ## options.daq ###
    # ##################

    # read in tags
    input_syntax = config['data']['input_syntax'].split('.')
    output_syntax = config['data']['output_syntax'].split('.')


    def create_folder(path):
        if not os.path.isdir(path):
            subprocess.call(['mkdir', '-p', path])

    def convert_file_name(file_name):
        '''
            Convert file_name from input_syntax to output_syntax
        '''
        # merge tags and token from file_name
        temp_in = dict(zip(input_syntax,
                       file_name[:file_name.find(ending)-1].split('.')))
        temp_out = []
        for tag in output_syntax:
            try:
                temp_out.append(temp_in[tag])
            except:
                temp_out.append(tag)
        temp_out.append(ending)
        return '.'.join(temp_out)

    # create folder for job
    create_folder(job_name)

    for particle in particle_types:
        # create subfolder for each dataset
        temp_dir = join(job_name, particle + systematics)
        create_folder(temp_dir)
        subprocess.call(['cp', join(dirname(argv[0]), basename(argv[0])),
                        join(job_name, basename(argv[0]))])

        with open(join(temp_dir,'dagman.config'), 'w') as dagman:
            # read template file
            with open(join(base_path,'resources', 'dagman_config.txt'), 'r') \
                    as temp_dagman:
                template = temp_dagman.read()
            # write template with filled in values from config
            dagman.write(template.format(max_jobs,
                                         max_jobs_per_interval,
                                         interval_length))

        job_file = 'OneJob.submit'
        with open(join(temp_dir, job_file), 'w') as onejob:
            # read template file
            with open(join(base_path, 'resources', 'OneJob_submit.txt'), 'r') \
                    as temp_onejob:
                template = temp_onejob.read()
            # write template with filled in values from config
            onejob.write(template.format(environment, ' '.join(arguments)))

        # write option list to .daq file
        # create input path from data set names (particle + systematics)
        with open(join(temp_dir,'options.dag'), 'w') as options:
            in_dir = config['settings']['inputfile'].format(particle+systematics)
            print("Creating jobs for {}".format(particle+systematics))
            for root, dirs, files in walk(in_dir):
                if 'log' in root:
                    continue
                for file_name in tqdm(files):
                    if ending in file_name and not file_name.startswith('Geo'):
                        job_id = job_name + '_' + \
                                 file_name[:file_name.find(ending)-1].replace('.', '_')
                        in_file = join(root, file_name)
                        # create folder if neccessary
                        out_path = config['settings']['outputfile'].format(particle+systematics)
                        create_folder(out_path)
                        out_file = join(out_path, convert_file_name(file_name))
                        option_string = ['{}="{}"'.format(arg, val) \
                                        for arg, val in \
                                        config['settings'].items() \
                                        if not 'put' in arg]
                        option_string.insert(0, '''JOB {} {}
VARS {} JOBNAME="{}" inputfile="{}" outputfile="{}"'''.format(
                                             job_id,
                                             job_file,
                                             job_id,
                                             job_name,
                                             in_file,
                                             out_file))
                        options.write(' '.join(option_string) + '\n')

if __name__ == '__main__':
    generate_DAGman_job(sys.argv[1:])
