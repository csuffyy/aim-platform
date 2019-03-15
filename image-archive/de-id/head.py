"""Main program for creating jobs for the cluster.

Creates a list of all dicom files found in the given folder (and subfolders).
Assigns all these files to groups. For each group, a .txt file will be created
that contains a list of all dicom files in that group. Creates the shell script
that will be submitted to the cluster. Also creates the shell script that will
submit the other shell scripts to the cluster.

(Uses load_elastic.py rather than scan.py in the next step.)
"""

import os
import math
import argparse
import uuid
import pickle
import time


def create_sub_sh(jobdir, num_groups):
    """Create shell script that will submit the other shell scripts.
    """
    with open(os.path.join(jobdir, 'subjobs.sh'), 'w') as f:
        for i in range(num_groups):
            fn = 'dcmfiles_{:05d}'.format(i)
            fn = os.path.join(jobdir, fn)
            f.write('qsub {}\n'.format(fn))
            f.write('sleep .1\n')  # To prevent too many commands too fast
    return


def create_job_sh(fn, jobdir):
    """Create shell script that will submit a subset of dicoms to cluster.

    Hard coded.

    Args:
        fn: Base file name.
    """
    with open(fn, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('\n')
        f.write('#PBS -l mem=8gb,vmem=8gb\n')
        f.write('#PBS -l nodes=1:ppn=1\n')
        f.write('#PBS -l walltime=00:40:00\n')  # Depends on size of the group
        f.write('#PBS -j oe\n')
        f.write('#PBS -o {}\n'.format(jobdir))
        f.write('\n')
        f.write('module load python/3.7.1_GDCM\n')
        # f.write('module load dcmtk/3.6.0\n')
        f.write('\n')
        f.write('source /home/chuynh/aim-platform/image-archive/environments/hpf/env.sh\n')
        f.write('source /home/chuynh/secrets.sh\n')
        f.write('\n')
        f.write('python /home/chuynh/aim-platform/image-archive/de-id/load_elastic.py '
            + fn + '.txt /hpf/largeprojects/diagimage_common/shared/thumbnails\n')
        f.write('\n')
    return


def create_txt_file(group, fn):
    """Creates .txt file that contains a list of all dicom files in that group.

    Args:
        group: List of dicom files.
        fn: Base file name.
    """
    with open(fn + '.txt', 'w') as f:
        # Write each file name to file
        for j in range(len(group)):
            f.write(group[j] + '\n')
    return


def create_mll(master_list, jobdir, num_dcm):
    """Creates master linking log using a dictionary and saves it to disk.

    Args:
        master_list: List of full path file names.
        jobdir: Where to save master linking log.
        num_dcm: Total number of dicom files.

    Returns:
        new_fns: List of new file names. Does not contain a directory in name.
            Same length as master_list.
    """
    mll = {}
    mybool = True
    while mybool:
        # Create a new random file name for each dicom
        new_fns = [str(uuid.uuid4()) for _ in range(num_dcm)]
        # Check if each random file name is unique
        if num_dcm > len(set(new_fns)):  # Not unique
            # This should never happen...
            print('The universe is conspiring against us! Trying again...')
        else:
            mybool = False

    # Adding the .dcm file extension
    new_fns = [new_fns[i] + '.dcm' for i in range(num_dcm)]

    # Adding entries to master linking log.
    for i in range(num_dcm):
        mll[new_fns[i]] = master_list[i]

    # Saves the mll with pickle
    mll_fn = os.path.join(jobdir, 'mll')
    with open(mll_fn, 'wb') as h:
        pickle.dump(mll, h, protocol=pickle.HIGHEST_PROTOCOL)

    return new_fns


def form_master_list(master_list, datadir):
    """Goes through folder and subfolders and forms a list dicom files.

    Args:
        master_list: List of all dicom files.
        datadir: The input directory to search.
    """
    # Get list of full path and filename
    entries = [os.path.join(datadir, i) for i in os.listdir(datadir)]

    for entry in entries:  # Loop through each entry
        if os.path.isfile(entry):  # If it is a file
            if entry.lower().endswith('.dcm'):
                # Dicom files must have this extension
                master_list.append(entry)  # Add to list
        elif os.path.isdir(entry):
            # Recursive
            form_master_list(master_list, entry)
    return


def main(jobdir, datadir, num):
    # Form list of all dicom files.
    # This list could be very large...
    master_list = []
    t0 = time.time()
    print('Making list of all dicom files... ', end='')
    form_master_list(master_list, datadir)
    print('Done making list.')
    print('Time to make list: {:.2f} s'.format(time.time() - t0))

    # Total number of dicom files
    num_dcm = len(master_list)
    print('{} dicom files found.'.format(num_dcm))

    # Create job directory if not exist. This will hold all generated files.
    if not os.path.isdir(jobdir):
        print('Making job directory.')
        os.makedirs(jobdir)

    # Create master linking log
    print('Creating master linking log.')
    t0 = time.time()
    new_fns = create_mll(master_list, jobdir, num_dcm)
    print('Time to make mll: {:.2f} s'.format(time.time() - t0))

    # Number of groups
    ng = math.ceil(num_dcm / num)

    # Assign dicom files to the groups. List of lists.
    groups = []
    for i in range(ng):
        # groups.append(new_fns[i*num:(i+1)*num])
        groups.append(master_list[i*num:(i+1)*num])

    print('Putting dicom files into {} groups.'.format(ng), end='')
    print(' Creating job shell scripts... ', end='')
    t0 = time.time()
    # For each group
    for i in range(ng):
        # Name of file. Assuming group number does not exceed 5 digits.
        fn = 'dcmfiles_{:05d}'.format(i)
        fn = os.path.join(jobdir, fn)

        # Current group of dicom files. List.
        group = groups[i]

        # Create .txt file containing a list of all dicom files in that group
        create_txt_file(group, fn)

        # Create shell script that will submit this subset of dicoms to cluster
        create_job_sh(fn, jobdir)

    print('Done.')
    print('Time to create all files: {:2f} s'.format(time.time() - t0))

    # Create shell script that will submit the other shell scripts.
    print('Creating script that will submit the jobs.')
    create_sub_sh(jobdir, ng)
    return


if __name__ == '__main__':
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Creates jobs.')
    # Positional arguments
    parser.add_argument('jobdir', help='Job directory.')
    parser.add_argument('datadir', help='Root directory of all dicoms.')
    # Optional arguments
    parser.add_argument('-n', '--num', type=int, default=10000,
                        help='Number of files per job.')
    # Parse command line arguments
    args = parser.parse_args()

    t0 = time.time()
    print('\nDirectory to put all generated files in: {}'.format(args.jobdir))
    print('Directory to search for dicom files: {}'.format(args.datadir))
    print('Number of files per job: {}'.format(args.num))
    main(args.jobdir, args.datadir, args.num)
    print('FINISHED.')
    print('Total time: {:.2f} s\n'.format(time.time() - t0))
