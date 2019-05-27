"""
PRECONDIITONS:
1. pip install datefinder
"""
import datefinder
from datetime import datetime

"""
@param known_dates: a list of strings of dates
@param text: the block of text that will be searched for dates
@return Returns if each date in known_dates is in text in the form or a list of booleans
"""
def datematcher(known_dates, text):

  returning = []
  matches = datefinder.find_dates(text)
  matches = list(matches)

  for date in known_dates :

    #convert each date in known_dates into a datetime object to be able to compare with the objects in matches
    datetime_object = datefinder.find_dates(date)
    datetime_object = list(datetime_object)

    if datetime_object[0] in matches:
      returning.append(True)
    else:
      returning.append(False)

  return returning

#For testing purposes
if __name__ == '__main__':
  string_with_dates = "entries are due by January 4th, 2017 at 8:00pm created 01/15/2005 by ACME Inc. and associates."
  dates = ["2017-01-04 20:00:00", "2005-01-15 00:00:00", "2017/01/04"]
  print(datematcher(dates, string_with_dates))