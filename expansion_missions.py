#!/usr/bin/env python

import os
import wget
import json
from datetime import datetime

# make the data directory
os.makedirs("./data", exist_ok=True)

def FileMoreThanSixHoursOld(filepath):
  dt_file = datetime.fromtimestamp(os.path.getmtime(filepath))
  age_delta = (datetime.now() - dt_file)
  return age_delta.total_seconds() / 3600 > 6.0

# check that the data files exist and are no more than six hours old
for datafile in ["factions.json","stations.json","systems_populated.json"]:
  filepath = "./data/" + datafile
  # if file is too old, delete it
  if os.path.exists(filepath) and FileMoreThanSixHoursOld(filepath):
    print("File %s too old, removing..." % filepath)
    os.remove(filepath)

  if not os.path.exists(filepath):
    print("Downloading file " + filepath)
    wget.download("https://eddb.io/archive/v6/" + datafile, out=filepath)
    
# load the system, station, and faction data
print("Loading station data...")
stations_file = open("./data/stations.json", 'r')
stations = json.loads(stations_file.read())
stations_file.close()

print("Loading system data...")
systems_file = open("./data/systems_populated.json", 'r')
systems = json.loads(systems_file.read())
systems_file.close()

print("Loading faction data...")
factions_file = open("./data/factions.json", 'r')
factions = json.loads(factions_file.read())
factions_file.close()

# index the faction names
faction_names_by_id = {f['id']:f['name'] for f in factions}

# identify systems with the appropriate mission giving stations
print("Filtering good mission giver systems...")
systems_with_large_orbitals = set()
for station in stations:
  if station['max_landing_pad_size'] == 'L' and \
      station['type_id'] in (3,7,8) and \
      station['distance_to_star'] < 1500 and \
      "Extraction" not in station['economies'] and \
      "Refinery" not in station['economies']:
    systems_with_large_orbitals.add(station['system_id'])

# identify systems with at least two factions in expansion (and only expansion) state
print("Finding juicy expansion factions...")
expansion_systems = {}
for system in systems:
  if('minor_factions_updated_at' in system and system['minor_factions_updated_at'] != None):
    active = 0
    faction_names = []
    modified = datetime.fromtimestamp(system['minor_factions_updated_at'])
    age = datetime.now() - modified
    age_hours = age.total_seconds() // 3600
    if age_hours < 48:
      for faction in system['minor_faction_presences']:
        if len(faction['active_states']) == 1 and faction['active_states'][0]['name'] == "Expansion":
            active += 1
            faction_names.append(faction_names_by_id[faction['minor_faction_id']])
      if active >= 2 and system['id'] in systems_with_large_orbitals:
        expansion_systems[system['name']] = {}
        expansion_systems[system['name']]['active'] = active
        expansion_systems[system['name']]['factions'] = faction_names

# print our findings
print("\n\nExpansion systems and factions:")
for (k,v) in expansion_systems.items():
  print("%s (%d)" % (k, v['active']))
  for f in v['factions']:
    print("   " + f)