'''
Author: Patrick Olsen
'''
import sys
import time
import struct
import argparse
from datetime import datetime
from Registry import Registry

class HelperFunctions(object):
    def __init__(self, hive=None):
        self.hive = hive

    def CurrentControlSet(self):
        select = Registry.Registry(self.hive).open("Select")
        current = select.value("Current").value()
        controlsetnum = "ControlSet00%d" % (current)
        return (controlsetnum)

    def EnumSIDs(self, sk, bam):
        sID = {}

        key_name = sk.name()
        keytimestamp = str(bam.timestamp())
        
        sID[key_name] = keytimestamp, sk.values()
        
        return sID

    def to_seconds(self, date):
        #https://stackoverflow.com/questions/6256703/convert-64bit-timestamp-to-a-readable-value
        s=float(date)/1e7 # convert to seconds
        seconds = s-11644473600 # number of seconds from 1601 to 1970
        newtime = time.ctime(seconds)
        returnedtime = datetime.strptime(newtime, '%a %b %d %H:%M:%S %Y')

        return returnedtime 

class BamBam(object):

    def __init__(self, hive, currentcontrolset):
        self.hive = hive
        self.currentcontrolset = currentcontrolset

    def findSIDs(self):
        bam = Registry.Registry(hive).open('%s\\Services\\bam\\UserSettings' % (self.currentcontrolset))

        for sk in bam.subkeys():
            yield HelperFunctions().EnumSIDs(sk, bam)


    def getValueData(self, val):
        for values in val:
            name = values.name()

            try:
                date = struct.unpack("<Q", values.value()[0:8])[0]
                converted_time = HelperFunctions().to_seconds(date)
            except TypeError:
                converted_time = None
                #continue

            yield (converted_time, name)

    def getValues(self, sids):
        for k,v in sids.items():
            for val in v:
                if isinstance(val, list):
                    for entries in self.getValueData(val):
                        yield str(entries[0]), k, entries[1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bam parser')
    parser.add_argument('-sys', '--system', required=True, 
        help='Path to SYSTEM hive.')
    args = parser.parse_args()

    hive = args.system

    currentcontrolset = HelperFunctions(hive).CurrentControlSet()

    times = []

    try:
        for sid in BamBam(hive, currentcontrolset).findSIDs():
            for entry in BamBam(hive, currentcontrolset).getValues(sid):
                times.append(entry)
    except Registry.RegistryKeyNotFoundException as e:
        print(e)
        exit(0)

    for time in times:
        print(time[0], time[1], time[2])

