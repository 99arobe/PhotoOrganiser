#!/usr/bin/python

# I still need to extract videos.

import sys
import os, shutil
import subprocess
import os.path
from datetime import datetime
from pathlib import Path

######################## Functions #########################

def photoDate(f):
  "Return the date/time on which the given photo was taken."
  
  photoDate = None

  try:
    photoDate = photoDateWithExiftool(f)
  except:
    print "Error getting date with exiftool for %s. Trying with sips instead" % f
    try:
      photoDate = photoDateWithSips(f)
    except:
      print "Error getting date with BOTH exiftool and sips. No date is available"
      raise

  return photoDate

def photoDateWithExiftool(f):
  "Uses exiftool to locate the creation date metadata for a given file. Slower, but more accurate than sips"

  # A useful command to print all available metadata for a given file to the console
  # exiftool -a -u -g1 [path to file] 

  # Check if 'exiftool' is installed
  from distutils.spawn import find_executable
  if find_executable("exiftool") is None:
    print "Cannot find exiftool. Please install exiftool"
    sys.exit()

  # Obtain metadata using exiftool for the date the file was originally created (used for naming the file later)
  # If the original date is not available, a series of fallbacks occurs for other possible dates
  ps = subprocess.Popen( ('exiftool', '-s', '-f', '-d', '%Y:%m:%dT%H:%M:%S', '-DateTimeOriginal', f), stdout=subprocess.PIPE)
  output = subprocess.check_output(('awk', '{print $3}'), stdin=ps.stdout)
  ps.wait()

  try:
    return datetime.strptime(output.strip('\n'), "%Y:%m:%dT%H:%M:%S")
  except:
    try:
      ps = subprocess.Popen( ('exiftool', '-s', '-f', '-d', '%Y:%m:%dT%H:%M:%S', '-MediaCreateDate', f), stdout=subprocess.PIPE)
      output = subprocess.check_output(('awk', '{print $3}'), stdin=ps.stdout)
      ps.wait()
      return datetime.strptime(output.strip('\n'), "%Y:%m:%dT%H:%M:%S")
    except:
      try:
        ps = subprocess.Popen( ('exiftool', '-s', '-f', '-d', '%Y:%m:%dT%H:%M:%S', '-FileCreateDate', f), stdout=subprocess.PIPE)
        output = subprocess.check_output(('awk', '{print $3}'), stdin=ps.stdout)
        ps.wait()
        return datetime.strptime(output.strip('\n'), "%Y:%m:%dT%H:%M:%S")
      except:
        try:
          ps = subprocess.Popen( ('exiftool', '-s', '-f', '-d', '%Y:%m:%dT%H:%M:%S', '-FileModifyDate', f), stdout=subprocess.PIPE)
          output = subprocess.check_output(('awk', '{print $3}'), stdin=ps.stdout)
          ps.wait()
          return datetime.strptime(output.strip('\n'), "%Y:%m:%dT%H:%M:%S")
        except:
          # No date obtained at all from exiftool
          raise

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

def fileExtensions(directory):
    "Identify all unique file formats in a given directory"
    extensions = set()
    for _, _, files in os.walk(directory):   
        for f in files:
            ext = Path(f).suffix.lower()
            extensions.add(ext)
    return extensions

###################### Main program ########################

# Where the photos are and where they're going.
#sourceDir = os.environ['HOME'] + '/Pictures/iPhone Incoming'
#/Users/aaronrobertson/Pictures/Photos Library.photoslibrary/originals
sourceDir = os.environ['HOME'] + '/Desktop/photos-sandbox'
#sourceDir = os.environ['HOME'] + '/Pictures/iPhone/Unsorted'
destDir = os.environ['HOME'] + '/Pictures/iPhone'
errorDir = destDir + '/Unsorted/'

# The format for the new file names.
fmt = "%Y-%m-%d %H-%M-%S"

# The problem files.
problems = []

# Get all the images in the source folder.
imageExtensions = ('.jpg', '.jpeg', '.heic', '.png', '.gif')
photos = find(sourceDir, imageExtensions)

# Get all the vidoes in the source folder.
videoExtensions = ('.mov', '.3gp', '.avi', '.mp4', '.m4v') 
videos = find(sourceDir, videoExtensions)

sourceDirSize = size(sourceDir)

print "%s of media found in: %s" % (sourceDirSize, sourceDir)
print "Searching the source directory for the following file extensions:"

knownExtensions = imageExtensions + videoExtensions
print knownExtensions

missing = []
for ext in fileExtensions(sourceDir):
  if ext not in knownExtensions:
    missing.append(ext)

if len(missing) > 0:
  print "WARNING: The source directory contains files with the following unrecognised file extensions:"
  print missing
  print "Consider adding support for the above extensions (using exiftool or similar) if they are valid media formats"
else:
  print "No unsupported file extensions were identified in directory. Continuing...."

print "-------------------------------------------------------------"
print "Found %s photos matching extensions: %s" % (len(photos), imageExtensions)
print "Found %s videos matching extensions: %s" % (len(videos), videoExtensions)
print "Preparing to copy into %s" % destDir

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
# their timestamps. If more than one photo or videos has the same timestamp,
# add suffixes 'a', 'b', etc. to the names. 
for item in photos + videos:
  original = item
  suffix = 1 # append to filenames when duplicates occur
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

    # Get the extension of the file here as they could be jpg or heic etc
    extension = os.path.splitext(item)[1]

    duplicate = thisDestDir + '/%s%s' % (newname, extension)
    while os.path.exists(duplicate):
      newname = pDate.strftime(fmt) + "_" + "%s" % suffix
      duplicate = destDir + '/%04d/%02d/%s%s' % (yr, mo, newname, extension)
      suffix += 1
    shutil.copy2(original, duplicate)
    writtenPhotos.append(item)
  except Exception as e:
    filename = os.path.basename(original)
    shutil.copy2(original, errorDir + filename)
    problems.append(item)
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
