#!/usr/bin/python3

# 2023-07 : ph.larduinat@wanadoo.fr
# Library 3.2.0

# Direct call of Netatmo API with authentication token
# Return a dictionary of body of Netatmo response

import lnetatmo

authorization = lnetatmo.ClientAuth()
rawData = lnetatmo.rawAPI(authorization, "gethomesdata")

print("Home name : home_id")
for h in rawData["homes"]:
  print(f"{h['name']} : {h['id']}")

print("Radio communication strength by home")
for h in rawData["homes"]:
  print(f"\nFor {h['name']}:")
  modules = lnetatmo.rawAPI(authorization, "homestatus", {"home_id" : h['id']})['home']
  if not 'modules' in modules:
    print("No modules available")
  else:
    print([(m['id'],m['rf_strength']) for m in modules['modules'] if 'rf_strength' in m])