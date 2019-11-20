import json
import requests
import sys

def _url(path):
        return 'https://dev-api.jsdn.io/v3' + path

def update_status(key, state, source, info):


        RestAPI = { "update":
            { "endpoint": "/testbed/test/update/", 
              "payload": {
                  "api_key": "",
                  "key": "", 
                  "status": { 
                      "state": "", 
                       "source":"", 
                       "message": "" 
                  }
                    
                 }}}

        payload = RestAPI['update']['payload']
        status = RestAPI['update']['payload']['status']

        status['state']=state
        status['source']=source
        status['message']='test'
        payload['api_key']='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IkUxQTM5RDgyQkE0NjNBNUI3ODVERUFEOUQwQ0RCRkZEMkY0RERFQTFDNzM5RDhGODc5RDhFOTE4N0Q4MzkzMUE0RkI5RDYxRjA2NzczRDUyMTA1QTE2Njc1NjgyNjhFRDJGQjYyNzQ2Nzg1ODAwRjkzMUQ3ODg1MzIyOUYzNTRFIiwiZW1haWwiOiJhZG1pbkBqdW1wbmV0LmNvbSIsImlhdCI6MTUzNjA5MzExMX0._1fnuQsb3OHzy6FTa-6zdIo1_q2fKYp5G6f_Hya6DMg'
        payload['key']=key
        payload['status']=status

        url = _url(RestAPI['update']['endpoint'] + key)
        print(url)

        msg = json.dumps(payload)

        print(msg)
        #msg = msg.encode()

        #print(msg)
        resp = requests.put(url, json=msg)
       
        print(resp)
        return resp

update_status('BB8F77FE3B5032F221C18E486C5FA5533F4F2CEEC83B2FD069C4C09B0818C3BDE865BF50CC6C975A109652DB32D8719CC244AE6F898B16FD703BED00880BF7D7', sys.argv[1], 'test-orchestrator', '')

