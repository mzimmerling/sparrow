import sys
import os
import re

# TODO EXCLUDE STUFF
min_pct = .30
pax_pct = .50


# Looks through the spark logs and gets percentile wait times

def get_wait_pctls(directory):
  times = []
  for f in os.listdir(directory):
    if not "wait" in f:
      continue
    lines = open(os.path.join(directory, f)).readlines()
    count = 0
    for k in lines:
      wait = k.split("waitTime=")[1].replace("ms\n", "")
      times.append(wait)
  if len(times) == 0:
    return ()
  print len(times)
  times = times[int(len(times) * .5) : int(len(times) * .75)]
  five = times[int(len(times) * .05)]
  fifty = times[int(len(times) * .5)]
  nintyfive = times[int(len(times) * .95)]
  nintynine = times[int(len(times) * .99)]  
  return (five, fifty, nintyfive, nintynine)

# Looks through the TPCH summaries and gets percentile response times
def get_pctls(directory):
  times = []
  for f in os.listdir(directory):
    if not "tpch" in f:
      continue
    lines = open(os.path.join(directory, f)).readlines()
    count = 0
    for k in lines:
      parts = k.split("\t")
      if parts[0] != "trial":
        continue
      count = count + 1
      times.append(int(parts[1]))
    if count < 100:
      return ()
  if len(times) == 0:
    return ()
  print len(times)
  times = times[int(len(times) * .5) : int(len(times) * .75)]
  print len(times)
  times.sort()
  five = times[int(len(times) * .05)]
  fifty = times[int(len(times) * .5)]
  nintyfive = times[int(len(times) * .95)]
  nintynine = times[int(len(times) * .99)]  
  return (five, fifty, nintyfive, nintynine)
      

def main(args):
  d = args[0]
  files = os.listdir(d)
  r = re.compile("((sparrow)|(mesos))_((\d+).*(\d)*)")
  resp_data = {}
  wait_data = {}
  for f in files:
    if os.path.isdir(os.path.join(d, f)):
      if re.match(r, f):
        m = re.match(r, f)
        sched = m.group(1)
        rate = m.group(4)

        resp_val = get_pctls(os.path.join(d, f)) 
        if resp_val == ():
          print "MISSING RESP DATA: %s" % os.path.join(d, f)
          continue
        key = sched
        if key not in resp_data:
          resp_data[key] = {}
        resp_data[key][rate] = resp_val

        wait_val = get_wait_pctls(os.path.join(d, f)) 
        if wait_val == ():
          print "MISSING WAIT DATA: %s" % os.path.join(d, f)
          continue
        key = sched
        if key not in wait_data:
          wait_data[key] = {}
        wait_data[key][rate] = wait_val

  for ((sched), values) in resp_data.items():
    f = open("%s_resp.txt" % (sched), 'w')
    f.write("load\t5\t50\t95\t99\n")
    for (load, res) in sorted(values.items(), key=lambda x: x[0]):
      f.write("%s\t%s\t%s\t%s\t%s\n" % (load, res[0], res[1], res[2], res[3]))
    f.close()

  for ((sched), values) in wait_data.items():
    f = open("%s_task_wait.txt" % (sched), 'w')
    f.write("load\t5\t50\t95\t99\n")
    for (load, res) in sorted(values.items(), key=lambda x: x[0]):
      f.write("%s\t%s\t%s\t%s\t%s\n" % (load, res[0], res[1], res[2], res[3]))
    f.close()

if __name__ == "__main__":
  main(sys.argv[1:])
