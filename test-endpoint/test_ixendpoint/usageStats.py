#!/usr/bin/env python3

import json
import logging

from datetime import datetime
from test_common.database import database
from test_common.util import Util

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


class usageStats:
    def __init__(self, hostName, endpoint, test_id):
        try:
            self.records = dict()
            self.sessionKeys = list()
            self.hostname = hostName
            self.endpoint = endpoint
            self.test_id = test_id

            self.db = database('testtier')
            self.db.connect()


        except Exception as e:
            logger.error("Error: {0}".format(e))

    def __del__(self):
        logger.error('Remove usageStats')
        del self.db
    
    def addEvents(self, action, data, section):

        try:

            self.records.clear()
            self.sessionKeys.clear()

            json_data = json.loads(data)

            d = dict(json_data['payload'])

            for key in d:
                if d[key]['session']['bps_in']['mean']:
                    self.obj = dict()
                    self.obj['date'] = str(datetime.now())[:-3]
                    self.obj['session_id'] = key
                    self.obj['test_id'] = self.test_id
                    self.obj['source'] = self.hostname
                    self.obj['op'] = json_data['op']
                    self.obj['name'] = 'jumpnet-{0}'.format(self.endpoint)
                    self.obj['raw_json'] = json.dumps(json_data['payload'][key])
                    self.extract(None, d[key], section)
                    self.extract(None, d[key], 'timestamp')
                    self.records[key] = self.obj

                self.sessionKeys.append(key)


        except Exception as e:
            logger.error("Error: {0}".format(e))

        self.insert('usagestats')

    def addOPEvent(self, data):

        try:

            self.records.clear()

            json_data = json.loads(data)
            
            dt = datetime.now()

            self.obj = dict()
            self.obj['date'] = str(dt)[:-3]
            self.obj['session_id'] = json_data.get('session')
            self.obj['test_id'] = self.test_id
            self.obj['source'] = self.hostname
            self.obj['op'] = json_data['op']
            self.obj['name'] = 'jumpnet-{0}'.format(self.endpoint)
            self.obj['raw_json'] = json.dumps(json_data.get('payload'))
            self.obj['timestamp_value'] = Util._seconds() 

            self.db.insert('usagestats', self.obj)
               
        except Exception as e:
            logger.error("Error: {0}".format(e))

        


    def getSessionKeys(self):
        return self.sessionKeys

    def extract(self, key, value, include):
        try:
            if isinstance(value, str):
                result = "{'" + key + "' : '" + value + "'}"
                print(result)
                self.obj[key] = value
                return

            if isinstance(value, int):
                result = "{'" + key + "' : " + str(value) + "}"
                print(result)
                self.obj[key] = value
                return

            if isinstance(value, float):
                result = "{'" + key + "' : " + str(value) + "}"
                print(result)
                self.obj[key] = value
                return

            if isinstance(value, tuple):
                result = "{'" + key + "' : " + value + "}"
                print(result)
                self.obj[key] = value
                return

            # todo build in some functionality to handle list different ways
            #   now just taking first value since thats all we need right now
            t = 0
            if isinstance(value, list):
                if value:
                    result = "{'" + key + "' : " + str(value[0]) + "}"
                    print(result)
                    self.obj[key] = value[0]
                else:
                    result = "{'"+key+"' : ''}"
                    print(result)
                    self.obj[key] = ''
                # get all
                # for i in value:
                #    self.extract(key+"_"+str(t),i)
                #    t = t + 1
                return

            if isinstance(value, dict):
                for i in value.keys():
                    if key:
                        key_i = key+"_" + i
                        self.extract(key_i, value[i], include)
                    else:
                        if i == include:
                            key_i = i
                            self.extract(key_i, value[i], include)

                return
        except Exception as e:
            logger.error("Error: {0}".format(e))


    def insert(self, table):
        try:
            logger.info('Insert Records into {0}'.format(table))

            for rec in self.records:
                logger.info('Insert into {0}: {1}'.format(table, self.records[rec]))
                self.db.insert(table, self.records[rec])
        except Exception as e:
            logger.error("Error: {0}".format(e))
