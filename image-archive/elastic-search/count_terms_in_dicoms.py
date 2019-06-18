import pandas as pd
import os
import pydicom
import numpy as np
from matplotlib import pyplot as plt
from uuid import UUID
import re

mri_directory = './mri_data/linking-anna-alex-abhi-2/'


class DatasetAnalyzer:
    def __init__(self, unique_keys, dicom_directory):
        self.keys = unique_keys
        self.root_dir = dicom_directory
        self.scans_list = os.listdir(mri_directory)
        self.organized_folders = {}
        self.dcm_dict = {}

    def read_dicoms(self):

        for folder in os.listdir(self.root_dir):
            folder = os.path.join(self.root_dir, folder)
            for scan in os.listdir(folder):
                dcm_scan = pydicom.dcmread(os.path.join(folder, scan))
                dcm_keys = dcm_scan.dir("")
                for key in dcm_keys:
                    value = str(dcm_scan.data_element(key)._value)
                    tag = str(dcm_scan.data_element(key).tag)
                    if tag not in self.dcm_dict:
                        self.dcm_dict[tag] = {}
                    if value not in self.dcm_dict[tag]:
                        self.dcm_dict[tag][value] = 0
                    self.dcm_dict[tag][value] += 1

    def quot(self, string):
        return "\"" + str(string) + "\""


    def write_dcm_dict(self, fn):

        def is_uuid(uuid):
            try:
                val = UUID(uuid, version=4)
                return True
            except ValueError:
                return False

        # dcm_keys = dcm_scan.dir("")
        # print(dcm_keys)
        # key_tuple = str((dcm_scan.PatientName,dcm_scan.AccessionNumber))
        # if key_tuple not in self.organized_folders.keys():
        # 	self.organized_folders[key_tuple] = [os.path.join(folder,scan)]
        # else:
        # 	self.organized_folders[key_tuple].append(os.path.join(folder,scan))
        f = open(fn, "w")

        # sort the lists
        value_count_list = []

        for tag, values in self.dcm_dict.items():
            if tag != "(7fe0, 0010)" \
                    and tag != "(0008, 0018)" \
                    and tag != "(0020, 0032)" \
                    and tag != "(0020, 1041)":
                # values -> [(value, count), ...]
                count_list = sorted(values.items(), key=lambda x: x[1])[::-1]
                value_count_list.append((tag, count_list))


        value_count_list = sorted(value_count_list, key=lambda x: x[1][0][1])
        value_count_list = value_count_list[::-1]
        # print(value_count_list)

        for tag, cl in value_count_list:
            print(cl[0][0])
            if len(str(cl[0][0])) > 1 \
                    and not re.match(r"^[\.0-9]+$", str(cl[0][0])) \
                    and not is_uuid(str(cl[0][0])) \
                    and str(cl[0][0])[0] != "[":
                for value, count in cl:
                    f.write(self.quot(tag) + "," + self.quot(value) + "," + self.quot(count) + "\n")

                f.write("\n")


        f.close()


dataset_analyzer = DatasetAnalyzer(['PatientName', 'AccessionNumber'], mri_directory)
dataset_analyzer.read_dicoms()
dataset_analyzer.write_dcm_dict("dicom_element_counts.csv")
# print(dataset_analyzer.organized_folders)
import pandas as pd
import os
import pydicom
import numpy as np
from matplotlib import pyplot as plt
from uuid import UUID
import re

mri_directory = './mri_data/linking-anna-alex-abhi-2/'


class DatasetAnalyzer:
    def __init__(self, unique_keys, dicom_directory):
        self.keys = unique_keys
        self.root_dir = dicom_directory
        self.scans_list = os.listdir(mri_directory)
        self.organized_folders = {}
        self.dcm_dict = {}

    def read_dicoms(self):

        for folder in os.listdir(self.root_dir):
            folder = os.path.join(self.root_dir, folder)
            for scan in os.listdir(folder):
                dcm_scan = pydicom.dcmread(os.path.join(folder, scan))
                dcm_keys = dcm_scan.dir("")
                for key in dcm_keys:
                    value = str(dcm_scan.data_element(key)._value)
                    tag = str(dcm_scan.data_element(key).tag)
                    if tag not in self.dcm_dict:
                        self.dcm_dict[tag] = {}
                    if value not in self.dcm_dict[tag]:
                        self.dcm_dict[tag][value] = 0
                    self.dcm_dict[tag][value] += 1

    def quot(self, string):
        return "\"" + str(string) + "\""


    def write_dcm_dict(self, fn):

        def is_uuid(uuid):
            try:
                val = UUID(uuid, version=4)
                return True
            except ValueError:
                return False

        # dcm_keys = dcm_scan.dir("")
        # print(dcm_keys)
        # key_tuple = str((dcm_scan.PatientName,dcm_scan.AccessionNumber))
        # if key_tuple not in self.organized_folders.keys():
        # 	self.organized_folders[key_tuple] = [os.path.join(folder,scan)]
        # else:
        # 	self.organized_folders[key_tuple].append(os.path.join(folder,scan))
        f = open(fn, "w")

        # sort the lists
        value_count_list = []

        for tag, values in self.dcm_dict.items():
            if tag != "(7fe0, 0010)" \
                    and tag != "(0008, 0018)" \
                    and tag != "(0020, 0032)" \
                    and tag != "(0020, 1041)":
                # values -> [(value, count), ...]
                count_list = sorted(values.items(), key=lambda x: x[1])[::-1]
                value_count_list.append((tag, count_list))


        value_count_list = sorted(value_count_list, key=lambda x: x[1][0][1])
        value_count_list = value_count_list[::-1]
        # print(value_count_list)

        for tag, cl in value_count_list:
            print(cl[0][0])
            if len(str(cl[0][0])) > 1 \
                    and not re.match(r"^[\.0-9]+$", str(cl[0][0])) \
                    and not is_uuid(str(cl[0][0])) \
                    and str(cl[0][0])[0] != "[":
                for value, count in cl:
                    f.write(self.quot(tag) + "," + self.quot(value) + "," + self.quot(count) + "\n")

                f.write("\n")


        f.close()


dataset_analyzer = DatasetAnalyzer(['PatientName', 'AccessionNumber'], mri_directory)
dataset_analyzer.read_dicoms()
dataset_analyzer.write_dcm_dict("dicom_element_counts.csv")
# print(dataset_analyzer.organized_folders)
import pandas as pd
import os
import pydicom
import numpy as np
from matplotlib import pyplot as plt
from uuid import UUID
import re

mri_directory = './mri_data/linking-anna-alex-abhi-2/'


class DatasetAnalyzer:
    def __init__(self, unique_keys, dicom_directory):
        self.keys = unique_keys
        self.root_dir = dicom_directory
        self.scans_list = os.listdir(mri_directory)
        self.organized_folders = {}
        self.dcm_dict = {}

    def read_dicoms(self):

        for folder in os.listdir(self.root_dir):
            folder = os.path.join(self.root_dir, folder)
            for scan in os.listdir(folder):
                dcm_scan = pydicom.dcmread(os.path.join(folder, scan))
                dcm_keys = dcm_scan.dir("")
                for key in dcm_keys:
                    value = str(dcm_scan.data_element(key)._value)
                    tag = str(dcm_scan.data_element(key).tag)
                    if tag not in self.dcm_dict:
                        self.dcm_dict[tag] = {}
                    if value not in self.dcm_dict[tag]:
                        self.dcm_dict[tag][value] = 0
                    self.dcm_dict[tag][value] += 1

    def quot(self, string):
        return "\"" + str(string) + "\""


    def write_dcm_dict(self, fn):

        def is_uuid(uuid):
            try:
                val = UUID(uuid, version=4)
                return True
            except ValueError:
                return False

        # dcm_keys = dcm_scan.dir("")
        # print(dcm_keys)
        # key_tuple = str((dcm_scan.PatientName,dcm_scan.AccessionNumber))
        # if key_tuple not in self.organized_folders.keys():
        # 	self.organized_folders[key_tuple] = [os.path.join(folder,scan)]
        # else:
        # 	self.organized_folders[key_tuple].append(os.path.join(folder,scan))
        f = open(fn, "w")

        # sort the lists
        value_count_list = []

        for tag, values in self.dcm_dict.items():
            if tag != "(7fe0, 0010)" \
                    and tag != "(0008, 0018)" \
                    and tag != "(0020, 0032)" \
                    and tag != "(0020, 1041)":
                # values -> [(value, count), ...]
                count_list = sorted(values.items(), key=lambda x: x[1])[::-1]
                value_count_list.append((tag, count_list))


        value_count_list = sorted(value_count_list, key=lambda x: x[1][0][1])
        value_count_list = value_count_list[::-1]
        # print(value_count_list)

        for tag, cl in value_count_list:
            print(cl[0][0])
            if len(str(cl[0][0])) > 1 \
                    and not re.match(r"^[\.0-9]+$", str(cl[0][0])) \
                    and not is_uuid(str(cl[0][0])) \
                    and str(cl[0][0])[0] != "[":
                for value, count in cl:
                    f.write(self.quot(tag) + "," + self.quot(value) + "," + self.quot(count) + "\n")

                f.write("\n")


        f.close()


dataset_analyzer = DatasetAnalyzer(['PatientName', 'AccessionNumber'], mri_directory)
dataset_analyzer.read_dicoms()
dataset_analyzer.write_dcm_dict("dicom_element_counts.csv")
# print(dataset_analyzer.organized_folders)
import pandas as pd
import os
import pydicom
import numpy as np
from matplotlib import pyplot as plt
from uuid import UUID
import re

mri_directory = './mri_data/linking-anna-alex-abhi-2/'


class DatasetAnalyzer:
    def __init__(self, unique_keys, dicom_directory):
        self.keys = unique_keys
        self.root_dir = dicom_directory
        self.scans_list = os.listdir(mri_directory)
        self.organized_folders = {}
        self.dcm_dict = {}

    def read_dicoms(self):

        for folder in os.listdir(self.root_dir):
            folder = os.path.join(self.root_dir, folder)
            for scan in os.listdir(folder):
                dcm_scan = pydicom.dcmread(os.path.join(folder, scan))
                dcm_keys = dcm_scan.dir("")
                for key in dcm_keys:
                    value = str(dcm_scan.data_element(key)._value)
                    tag = str(dcm_scan.data_element(key).tag)
                    if tag not in self.dcm_dict:
                        self.dcm_dict[tag] = {}
                    if value not in self.dcm_dict[tag]:
                        self.dcm_dict[tag][value] = 0
                    self.dcm_dict[tag][value] += 1

    def quot(self, string):
        return "\"" + str(string) + "\""


    def write_dcm_dict(self, fn):

        def is_uuid(uuid):
            try:
                val = UUID(uuid, version=4)
                return True
            except ValueError:
                return False

        # dcm_keys = dcm_scan.dir("")
        # print(dcm_keys)
        # key_tuple = str((dcm_scan.PatientName,dcm_scan.AccessionNumber))
        # if key_tuple not in self.organized_folders.keys():
        # 	self.organized_folders[key_tuple] = [os.path.join(folder,scan)]
        # else:
        # 	self.organized_folders[key_tuple].append(os.path.join(folder,scan))
        f = open(fn, "w")

        # sort the lists
        value_count_list = []

        for tag, values in self.dcm_dict.items():
            if tag != "(7fe0, 0010)" \
                    and tag != "(0008, 0018)" \
                    and tag != "(0020, 0032)" \
                    and tag != "(0020, 1041)":
                # values -> [(value, count), ...]
                count_list = sorted(values.items(), key=lambda x: x[1])[::-1]
                value_count_list.append((tag, count_list))


        value_count_list = sorted(value_count_list, key=lambda x: x[1][0][1])
        value_count_list = value_count_list[::-1]
        # print(value_count_list)

        for tag, cl in value_count_list:
            print(cl[0][0])
            if len(str(cl[0][0])) > 1 \
                    and not re.match(r"^[\.0-9]+$", str(cl[0][0])) \
                    and not is_uuid(str(cl[0][0])) \
                    and str(cl[0][0])[0] != "[":
                for value, count in cl:
                    f.write(self.quot(tag) + "," + self.quot(value) + "," + self.quot(count) + "\n")

                f.write("\n")


        f.close()


dataset_analyzer = DatasetAnalyzer(['PatientName', 'AccessionNumber'], mri_directory)
dataset_analyzer.read_dicoms()
dataset_analyzer.write_dcm_dict("dicom_element_counts.csv")
# print(dataset_analyzer.organized_folders)
import pandas as pd
import os
import pydicom
import numpy as np
from matplotlib import pyplot as plt
from uuid import UUID
import re

mri_directory = './mri_data/linking-anna-alex-abhi-2/'


class DatasetAnalyzer:
    def __init__(self, unique_keys, dicom_directory):
        self.keys = unique_keys
        self.root_dir = dicom_directory
        self.scans_list = os.listdir(mri_directory)
        self.organized_folders = {}
        self.dcm_dict = {}

    def read_dicoms(self):

        for folder in os.listdir(self.root_dir):
            folder = os.path.join(self.root_dir, folder)
            for scan in os.listdir(folder):
                dcm_scan = pydicom.dcmread(os.path.join(folder, scan))
                dcm_keys = dcm_scan.dir("")
                for key in dcm_keys:
                    value = str(dcm_scan.data_element(key)._value)
                    tag = str(dcm_scan.data_element(key).tag)
                    if tag not in self.dcm_dict:
                        self.dcm_dict[tag] = {}
                    if value not in self.dcm_dict[tag]:
                        self.dcm_dict[tag][value] = 0
                    self.dcm_dict[tag][value] += 1

    def quot(self, string):
        return "\"" + str(string) + "\""


    def write_dcm_dict(self, fn):

        def is_uuid(uuid):
            try:
                val = UUID(uuid, version=4)
                return True
            except ValueError:
                return False

        # dcm_keys = dcm_scan.dir("")
        # print(dcm_keys)
        # key_tuple = str((dcm_scan.PatientName,dcm_scan.AccessionNumber))
        # if key_tuple not in self.organized_folders.keys():
        # 	self.organized_folders[key_tuple] = [os.path.join(folder,scan)]
        # else:
        # 	self.organized_folders[key_tuple].append(os.path.join(folder,scan))
        f = open(fn, "w")

        # sort the lists
        value_count_list = []

        for tag, values in self.dcm_dict.items():
            if tag != "(7fe0, 0010)" \
                    and tag != "(0008, 0018)" \
                    and tag != "(0020, 0032)" \
                    and tag != "(0020, 1041)":
                # values -> [(value, count), ...]
                count_list = sorted(values.items(), key=lambda x: x[1])[::-1]
                value_count_list.append((tag, count_list))


        value_count_list = sorted(value_count_list, key=lambda x: x[1][0][1])
        value_count_list = value_count_list[::-1]
        # print(value_count_list)

        for tag, cl in value_count_list:
            print(cl[0][0])
            if len(str(cl[0][0])) > 1 \
                    and not re.match(r"^[\.0-9]+$", str(cl[0][0])) \
                    and not is_uuid(str(cl[0][0])) \
                    and str(cl[0][0])[0] != "[":
                for value, count in cl:
                    f.write(self.quot(tag) + "," + self.quot(value) + "," + self.quot(count) + "\n")

                f.write("\n")


        f.close()


dataset_analyzer = DatasetAnalyzer(['PatientName', 'AccessionNumber'], mri_directory)
dataset_analyzer.read_dicoms()
dataset_analyzer.write_dcm_dict("dicom_element_counts.csv")
# print(dataset_analyzer.organized_folders)

