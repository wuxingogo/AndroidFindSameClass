import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
import sys
import time

from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    AdaptiveETA, FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, \
    SimpleProgress, Timer

def _unzip(name):
  destination = tempfile.mkdtemp()
  with zipfile.ZipFile(name) as f:
    f.extractall(destination)
  return destination

def _class_files(path):
  #print "class_files:" + path
  classes = []
  for root, dirs, files in os.walk(path):
    for file in files:
      if file.endswith('.class'):
        classes.append(os.path.join(root, file))
        #print root
  return classes

def _aar_files(path):
  aar_files = []
  for root, dirs, files in os.walk(path):
    for file in files:
      if file.endswith('.aar'):
        aar_files.append(os.path.join(root, file))
  return aar_files

def process_archive(temp_folder, jar):
  jar_basename = os.path.splitext(os.path.basename(jar))[0]
  filepath_hash = hex(hash(jar))[-8:]
  name = '%s_%s' % (jar_basename, filepath_hash)

  jar_stat = os.stat(jar)
  archive_folder = os.path.join(temp_folder, name)
  os.mkdir(archive_folder)

  unaar = None
  if jar.endswith('.aar'):
    unaar = _unzip(jar)
    jar = os.path.join(unaar, 'classes.jar')

  unjar = _unzip(jar)
  classes = _class_files(unjar)
  info = _javap_public(classes)
  infos = _split_info_into_infos(info)

  for _class in classes:
      #same class name
      # paths = _class.split("/")
      # length = len(paths)
      # class_name = paths[length-1]


      class_name = _class.replace(unjar, "")
      # print class_name
      if class_dict.__contains__(class_name) == False:
        class_dict[class_name] = []
      if(class_dict[class_name].__contains__(name)) == False:
        class_dict[class_name].append(name)




  _write_infos_to_temp(archive_folder, jar_stat, infos)

  shutil.rmtree(unjar)
  if unaar is not None:
    shutil.rmtree(unaar)

  return archive_folder

def _chunks(items, chunk_size):
  for i in range(0, len(items), chunk_size):
    yield items[i:i + chunk_size]


def _javap_public(files):
  results = []
  for chunk in _chunks(files, 200):
    results.append(str(subprocess.check_output(['javap', '-public'] + chunk)))
  return '\n'.join(results)


def _split_info_into_infos(info):
  original = re.findall(r'Compiled from ".*?\.(?:java|groovy)"\n.*?\n(?:  .*\n)*}\n', info,
                        flags=re.MULTILINE)
  infos = {}
  for info in original:
    lines = str(info).split('\n')[1:]
    header = lines[0]
    if not header.startswith('public '):
      continue
    match = re.match(r'(?:public |abstract |class |interface |final )+([^ ]+) .*', header)
    name = match.group(1)
    infos[name] = '\n'.join(lines)
  return infos


def _write_infos_to_temp(temp_folder, original_stat, infos):
  times = (original_stat[stat.ST_ATIME], original_stat[stat.ST_MTIME])

  for name, info in infos.items():
    out = os.path.join(temp_folder, name)
    with open(out, 'w') as f:
      f.write(info)
    os.utime(out, times)


class_dict = {}
def _main(folder):
  #print folder
  temp_folder = tempfile.mkdtemp()
  aar_files = _aar_files(folder)
  aar_count = len(aar_files)
  print aar_count
  iter_index = 0

  pbar = ProgressBar(widgets=[Percentage(), Bar('#','|||Percent|||')], maxval=aar_count).start()


  for aar in aar_files:
    extra_folder = process_archive(temp_folder, aar)
    iter_index +=1
    iter_index / aar_count
    pbar.update(iter_index)
  pbar.finish()

  for key, _classes in class_dict.iteritems():
    if len(_classes) > 1:

      print '============'
      print key
      for _class in _classes:
          print '    ' + _class
      print '============'
  print "execute finish."



if __name__ == '__main__':
  _main(sys.argv[1])