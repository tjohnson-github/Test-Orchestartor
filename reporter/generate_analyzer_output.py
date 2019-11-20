# Todo Implement
#
# This file needs to load the provided test-id data from the database and generate an analyzer.json file

import argparse
from test_common.database import database

parser = argparse.ArgumentParser()
parser.add_argument("test_id")
parser.add_argument("output_file")
args = parser.parse_args()
test_id = args.test_id
output_path = args.output_file
print("Running with test_id: {tid} output_path: {out}".format(tid=test_id, out=output_path))


dbTestTier = database('testtier')
if not dbTestTier.connect():
    print("Could not connect to Database!")
else:
    data = dbTestTier.QueryToJson('usagestats', test_id)

if not data:
    print("No Usage stat Data Found!")
else:
    text_file = open(output_path, "w")
    text_file.write(data)
    text_file.close()
    print("Return json: {0}".format(data))
