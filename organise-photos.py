#!/usr/bin/python

## I still need to extract videos. I can get the exif data using exiftool rather than sips
## I've got the basics of a command comment out below but i need to get python to call it with a pipe
## and then extract the right date. i should also add a fallback to get file creation date or modification
## date as well. then do the same for movies

import sys
import os, shutil
import subprocess
import os.path
from datetime import datetime

######################## Functions #########################

def photoDate(f):
  "Return the date/time on which the given photo was taken."
  return photoDateWithExiftool(f)
  #return photoDateWithSips(f)

def photoDateWithExiftool(f):
  "Uses exiftool to locate the creation date metadata for a given file. Slower, but more accurate than sips"
  ps = subprocess.Popen( ('exiftool', '-s', '-f', '-d', '%Y:%m:%dT%H:%M:%S', '-FileCreateDate', f), stdout=subprocess.PIPE)
  output = subprocess.check_output(('awk', '{print $3}'), stdin=ps.stdout)
  ps.wait()

  return datetime.strptime(output.strip('\n'), "%Y:%m:%dT%H:%M:%S")

def photoDateWithSips(f):
  "Uses sips to locate the creation date metadata for a given file. Faster, but less accurate than exiftool"
  cDate = subprocess.check_output(['sips', '-g', 'creation', f])
  cDate = cDate.split('\n')[1].lstrip().split(': ')[1]
  return datetime.strptime(cDate, "%Y:%m:%d %H:%M:%S")

def size(path):
    "Disk usage in human readable format (e.g. '2.1GB')"
    return subprocess.check_output(['du','-sh', path]).split()[0].decode('utf-8')

def find(directory, extensions):
    "Find files in the directory and sub directories matching the tuple of extensions"
    found = []

    for roots,dirs,files in os.walk(directory):
        for file in files:
            if file.lower().endswith(extensions):
                found.append(os.path.join(roots,file))

    return found


###################### Main program ########################

# Where the photos are and where they're going.
#sourceDir = os.environ['HOME'] + '/Pictures/iPhone Incoming'
#/Users/aaronrobertson/Pictures/Photos Library.photoslibrary/originals
sourceDir = os.environ['HOME'] + '/Desktop/backup_Photos Library.photoslibrary/masters'
destDir = os.environ['HOME'] + '/Pictures/iPhone'
errorDir = destDir + '/Unsorted/'

# The format for the new file names.
fmt = "%Y-%m-%d %H-%M-%S"

# The problem files.
problems = []

# Get all the images in the source folder.
imageExtensions = ('.jpg', '.jpeg')
photos = find(sourceDir, imageExtensions)

# Get all the vidoes in the source folder.
videoExtensions = ('.mov')
videos = find(sourceDir, videoExtensions)

sourceDirSize = size(sourceDir)
print "%s of media found in: %s" % (sourceDirSize, sourceDir)
print "Found %s photos matching extensions: %s" % (len(photos), imageExtensions)
print "Found %s videos matching extensions: %s" % (len(videos), videoExtensions)
print "Preparing to copy into %s" % destDir

print "%s" % videos

# Prepare to output as processing occurs
lastMonth = 0
lastYear = 0

# Create the destination folder if necessary
if not os.path.exists(destDir):
  os.makedirs(destDir)
if not os.path.exists(errorDir):
  os.makedirs(errorDir)

writtenPhotos = []

# Copy photos into year and month subfolders. Name the copies according to
# their timestamps. If more than one photo has the same timestamp, add
# suffixes 'a', 'b', etc. to the names. 
for photo in photos:
  original = photo
  suffix = 'a'
  try:
    pDate = photoDate(original)
    yr = pDate.year
    mo = pDate.month

    if not lastYear == yr or not lastMonth == mo:
      #sys.stdout.write('\nProcessing %04d-%02d...\n' % (yr, mo))
      lastMonth = mo
      lastYear = yr
    else:
      sys.stdout.write('.')
    
    newname = pDate.strftime(fmt)
    thisDestDir = destDir + '/%04d/%02d' % (yr, mo)
    if not os.path.exists(thisDestDir):
      os.makedirs(thisDestDir)

    duplicate = thisDestDir + '/%s.jpg' % (newname)
    while os.path.exists(duplicate):
      newname = pDate.strftime(fmt) + suffix
      duplicate = destDir + '/%04d/%02d/%s.jpg' % (yr, mo, newname)
      suffix = chr(ord(suffix) + 1)
    shutil.copy2(original, duplicate)
    writtenPhotos.append(photo)
  except Exception:
    filename = os.path.basename(original)
    shutil.copy2(original, errorDir + filename)
    problems.append(photo)
  except:
    sys.exit("Execution stopped.")

destDirSize = size(destDir)
errorDirSize = size(errorDir)

print "\nSuccessfully wrote %s files to %s which holds %s" % (len(writtenPhotos), destDir, destDirSize)

# Report the problem files, if any.
if len(problems) > 0:
  print "Warning: Found %s problem files (%s) with missing creation date EXIF data" % (len(problems), errorDirSize)
  #print "\n".join(problems)
  print "These can be found in: %s" % errorDir

# Write paths of successes and failures to some txt files for reference
with open('errors.txt', 'w') as f:
    for item in problems:
        f.write("%s\n" % item)

with open('written.txt', 'w') as f:
    for item in writtenPhotos:
        f.write("%s\n" % item)

print "\nDone"
