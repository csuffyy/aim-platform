# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 11:50:37 2019

@author: Zitian Zhang (Jordan)

Usage:
python3 image-archive/de-id/parse_all_colons.py image-archive/reports/sample/
"""

import glob
import sys
import re
import csv
import os

from dateparser.search import search_dates


def csv_append(output_dict):
  with open(output_csv, mode='a',newline='') as csv_file: 
    fieldnames = output_dict.keys()
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(output_dict) 

def csv_newfile(output_dict):
  with open(output_csv, mode='w+',newline='') as csv_file: 
    fieldnames = output_dict.keys()
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(output_dict)

      
def extract_value(text, output_dict):
  result = ''
  if ':' in text:
    split_text = re.split(r':', text, maxsplit=1) #only split once
  else:
    return
  result = split_text[1].strip()
  label = split_text[0].strip()        
  output_dict[label] = result
     
def split_sections(string):
  report, footer = re.split(r'Transcribed on',string, maxsplit=1,
                            flags=re.IGNORECASE)
  footer ='Transcribed on' + footer
  header, report = re.split(r'Radiological Report', report, maxsplit=1, 
                            flags=re.IGNORECASE)
  header = header + '\n' + footer
  return header, report  

def format_report(report):
  report = report.strip().strip('-').split('\n')
  report = [j for j in report if j]
  line = ''
  output = []
  for j in range(len(report)):
    if report[j].strip():
      if ':' in report[j]:
        if line.strip():
          output.append(line)
        line = report[j]
      else:
        line += report[j]
  output.append(line)
  return output

def find_and_fix_dates(report):
  '''Replace colons to semicolons in dates so that we can use the remaining colons as key value indicators.'''
  matches = search_dates(report) # Documentation: https://github.com/scrapinghub/dateparser/blob/master/dateparser/search/__init__.py#L9

  for (match, dateobj) in matches:
    if ':' in match:
      match_index = report.find(match)
      report = report[:match_index] + match.replace(':',';') + report[match_index + len(match):]

  return report

def process_file(filename):
  '''main code for report parser
  assumes the report only has colon behind each label, 
  thus colon appears in timestamps must be replaced beforehand.'''
  with open(filename, 'rb') as f:
    raw = f.read()
    raw = raw.decode('utf-8','ignore')

  report_with_consistent_dates = find_and_fix_dates(raw)
  header, report = split_sections(report_with_consistent_dates)
  output_dict = {'Raw': raw}
  output_dict['Report_Raw'] = report
  output_dict['Report'] = report.strip().strip('-').strip('\n').replace('\n','  ')
  header = re.split(r'\n|\t|\s{3,}', header)  #Split header into 'A:B's
  report = format_report(report)
  header_report = header+report
  for i in header_report:
    if i:
      extract_value(i.strip().strip('-'), output_dict)  
  return output_dict
    
if __name__ == '__main__':
  input_folder = sys.argv[1] if len(sys.argv) > 1 else './sample'
  files = glob.iglob('%s/**/*.txt' % input_folder, recursive=True)
  for filename in files:
    output_dict = process_file(filename)
