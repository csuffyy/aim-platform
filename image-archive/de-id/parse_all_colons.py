# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 11:50:37 2019

@author: Zitian Zhang (Jordan)
"""

import re
import csv
import os

#prevdir = os.getcwd()
#os.chdir(os.path.expanduser('sample'))
#files = os.listdir()
#df = pd.read_csv(files[0], sep='\t+\r', header=None)
#os.chdir(prevdir)




def csv_append(output_dict):
  with open('output/test.csv', mode='a',newline='') as csv_file: 
    fieldnames = output_dict.keys()
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(output_dict) 

def csv_newfile(output_dict):
  with open('output/test.csv', mode='w+',newline='') as csv_file: 
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
     
def split_raw(string):
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

def process_file(filename):
  '''main code for report parser
  assumes the report only has colon behind each label, 
  thus colon appears in timestamps must be replaced beforehand.'''
  with open(filename, 'r') as f:
    raw = f.read()
    print(raw)
  header, report = split_raw(raw)
  output_dict = {'Raw': raw}
  output_dict['Report'] = report.strip().strip('-').strip('\n').replace('\n','  ')
  header = re.split(r'\n|\t|\s{3,}', header)  #Split header into 'A:B's
  report = format_report(report)
  header_report = header+report
  for i in header_report:
    if i:
      extract_value(i.strip().strip('-'), output_dict)  
  return output_dict
    
if __name__ == '__main__':
  files = os.listdir('sample')
  for file in files:
    filename = os.path.join('sample',file)
    output_dict = process_file(filename)
    if os.path.exists('output/test.csv'):
      csv_append(output_dict)
    else:
      csv_newfile(output_dict)




