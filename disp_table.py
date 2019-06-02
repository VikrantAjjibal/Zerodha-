import cherrypy
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))


class HelloWorld(object):
    @cherrypy.expose
    def index(self):
        tmpl = env.get_template('display_table.html')
        #Download Zip file
        import requests
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)
        zipfilename = "EQ"+yesterday.strftime('%d%m%y')+"_CSV.zip"
        url = 'https://origin-www.bseindia.com/download/BhavCopy/Equity/'+zipfilename
        content = requests.get(url)
        
        # unzip the content
        from io import BytesIO
        from zipfile import ZipFile
        f = ZipFile(BytesIO(content.content))
        f.extractall()
        
        #Reading from the CSV
        import pandas as pd
        df = pd.read_csv(f.namelist()[0], skipinitialspace=True, usecols=['SC_NAME', 'SC_CODE', 'OPEN', 'HIGH', 'LOW', 'CLOSE'])
        df = df.sort_values(by=['CLOSE', 'SC_CODE', 'OPEN', 'HIGH', 'LOW', 'SC_NAME'], ascending=[False,False,False,False,False,True])
        
        #Converting dataframe to Dictionary 
        df_dict = df.to_dict('list')
        
        #Pushing the Dictionary to Redis 
        import redis
        import json
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        rval = json.dumps(df_dict)
        r.set('key', rval)
        
        #Retrieving data from Redis
        data = r.get('key')
        result = json.loads(data)
        return tmpl.render(result = result)
        
    index.exposed = True

# bind to all IPv4 interfaces
cherrypy.config.update({'server.socket_host': '127.0.0.1'})
cherrypy.quickstart(HelloWorld())