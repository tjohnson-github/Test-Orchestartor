import json

counter_id=0


def fileToJson(file):
        global counter_id
        counter_id += 1
        data = ''
        
        try:
           

            with open(file) as json_data:
              data =  json.load(json_data)

              data["counter"] = str(counter_id)

        except Exception as e:
            print(e)

        return data

