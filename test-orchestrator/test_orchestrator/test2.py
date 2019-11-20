import os
import json
import requests

api_key = os.environ['API_KEY']


# REST API Calls
RestAPI = {  
           "update":{  
              "endpoint": "/testbed/test/update/",
              "payload": { 
                 "api_key": "", 
                 "status": {  
                    "state": "",
                    "source": ""
                 }
              }
           }
           

        }


def _url(path):
        return 'https://dev-api.jsdn.io/v3' + path


def update_status(key, state, source, info="", results=None):
        resp = None

        try:

            payload = RestAPI['update']['payload']
            status = RestAPI['update']['payload']['status']

            status['state'] = state.lower()
            status['source'] = source
            if info != "":
               status['message']=info
            payload['api_key'] = api_key
            payload['key'] = key
            payload['status'] = status
            if results:
                payload['results'] = results

            url = _url(RestAPI['update']['endpoint'] + key)

            msg = json.dumps(payload)

            resp = requests.put(url, json=msg)

            if resp:
                print("resp object not None type")
            

            if resp.status_code!=200:
                print("REST API Error {0}".format(resp))
                print(" Url: {0}".format(url))
                print(" Json: {0}".format(msg))

        except Exception as e:
            print("\n***************   Error *********\n")
            print(e)

        return resp

#resp = update_status('CDAF8A3D97D604DC516E353C694B857BFC65C02CD5A3B9A900F89F8ECFE1B86808FA380B73BE4D41933F61BF5D116EBD2E90D97B94FFD61E617920D5831B2E26', 'success', 'test-orchestrator', info='test')

key='CDAF8A3D97D604DC516E353C694B857BFC65C02CD5A3B9A900F89F8ECFE1B86808FA380B73BE4D41933F61BF5D116EBD2E90D97B94FFD61E617920D5831B2E26'
url = _url('/testbed/test/raw/' + key)
payload = dict()
payload['key'] = key
payload['api_key'] = api_key
msg = json.dumps(payload)
print(" Url: {0}".format(url))
print(" Json: {0}".format(msg))

resp = requests.get(url,msg, headers={'Authorization': api_key }) 
print(resp)
print(resp.status_code)
obj = resp.json()

config = obj.get('test_config')
print(config)
instructionSet = config.get('instruction_set').get('instructions')

print(instructionSet)

commands = dict()

for instruction  in instructionSet:
  method = instruction.get('method')
  order = instruction.get('op_order')
  payload = instruction.get('payload')
  key = '{0}_{1}'.format(method,order)
  commands[key] = payload 
  print("Method: {0}".format(method)) 

print(commands)


print("Test Name: {0}".format(config.get('name')))
print("num clients: {0}".format(config.get('num_clients')))

