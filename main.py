import webapp2
import json
import datetime
from google.appengine.ext import ndb

##########       HELPER     ########## 
#source: https://code-maven.com/serialize-datetime-object-as-json-in-python
def dateConverter(o):
    if isinstance(o, datetime.date):
        return o.__str__()

##########       OBJECTS     ########## 
class Slip(ndb.Model):
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date = ndb.DateProperty()
    #optional : departure history (list)

class SlipNumber(ndb.Model):
    number = ndb.IntegerProperty()

class Boat(ndb.Model):
    #TODO: make name unique
    name = ndb.StringProperty(required=True)
    type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty()
    slipID = ndb.StringProperty()

##########       ROUTES     ########## 
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')

class Slips(webapp2.RequestHandler):
    def get(self):
       #source: https://cloud.google.com/appengine/docs/standard/python/ndb/queryclass
        qry = Slip.query()
        outString = "["
        for slip in qry:
            slip_dict = slip.to_dict()
            slip_dict['self'] = '/slips/' + slip.key.urlsafe()
            slip_dict['id'] = slip.key.urlsafe()
            outString = outString + json.dumps(slip_dict, default = dateConverter) + ', '
        if qry.get():
            outString = outString[:-2]
        outString = outString + ']'
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(outString)


    def post(self):
        slipNum = SlipNumber.query().get()
        if slipNum == None:
            slipNum = SlipNumber(number=1)
        new_slip = Slip(number=slipNum.number, current_boat=None, arrival_date=None)
        slipNum.number = slipNum.number + 1
        slipNum.put()
        new_slip.put()
        slip_dict = new_slip.to_dict()
        slip_dict['self'] = '/slips/' + new_slip.key.urlsafe()
        slip_dict['id'] = new_slip.key.urlsafe()
        self.response.write(json.dumps(slip_dict, default = dateConverter))

class Boats(webapp2.RequestHandler):
    def get(self):
        #source: https://cloud.google.com/appengine/docs/standard/python/ndb/queryclass
        qry = Boat.query()
        outString = "["
        for boat in qry:
            boat_dict = boat.to_dict()
            boat_dict['self'] = '/boats/' + boat.key.urlsafe()
            boat_dict['id'] = boat.key.urlsafe()
            boat_dict['slip'] = None
            if boat.slipID:
                slip = ndb.Key(urlsafe = boat.slipID).get()
                boat_dict['slip'] = '/slips/' + slip.key.urlsafe()
            outString = outString + json.dumps(boat_dict, default = dateConverter) + ', '
        if qry.get():
            outString = outString[:-2]
        outString = outString + ']'
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(outString)

    def post(self):
        bData = json.loads(self.request.body)
        new_boat = Boat(name=bData['name'], type=bData['type'], length=bData['length'])
        new_boat.at_sea = True 
        new_boat.slipID = None
        new_boat.put()
        boat_dict = new_boat.to_dict()
        boat_dict['self'] = '/boats/' + new_boat.key.urlsafe()
        boat_dict['id'] = new_boat.key.urlsafe()
        self.response.write(json.dumps(boat_dict, default = dateConverter))

class BoatHandler(webapp2.RequestHandler):
   def get(self, id=None):
        if id:
            boat = ndb.Key(urlsafe = id).get()
            if boat:
                boat_dict = boat.to_dict()
                boat_dict['self'] = '/boats/' + id
                boat_dict['id'] = id
                self.response.write(json.dumps(boat_dict, default = dateConverter))
            else:
                self.response.status = 403
                self.response.write("No boat found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

   def put(self, id=None):
        if id:
            boat = ndb.Key(urlsafe = id).get()
            if boat == None:
                self.response.status = 400
                self.response.write("No boat found")
                return
            bData = json.loads(self.request.body)
            if 'name' in bData:
                boat.name = bData['name']
            if 'type' in bData:
                boat.name = bData['type']
            if 'length' in bData:
                boat.name = bData['length']
            if 'at_sea' in bData:
                #send boat to sea
                if bData['at_sea'] == True:
                    #boat is docked
                    if boat.at_sea == False:
                        slip = ndb.Key(urlsafe = boat.slipID).get()
                        if slip != None:
                            boat.at_sea = True
                            boat.slipID = None
                            slip.current_boat = None
                            slip.put()
                            boat.put()
                            self.response.status = 204
                            self.response.write("Boat now at sea")
                        else:
                            self.response.status = 403
                            self.response.write("Could not find slip")
                    #boat already at sea
                    else:
                        self.response.status = 403
                        self.response.write("Boat already at sea")
                #dock boat
                else:
                    if 'slipID' in bData:
                        if boat.at_sea == True:
                            slip = ndb.Key(urlsafe = bData['slipID']).get()
                            if slip == None:
                                self.response.status = 403
                                self.response.write("No slip found")
                            elif slip.current_boat != None:
                                self.response.status = 403
                                self.response.write("Slip is occupied")
                            else:
                                slip.current_boat = boat.key.urlsafe()
                                boat.slipID = slip.key.urlsafe()
                                boat.at_sea = False
                                slip.put()
                                boat.put()
                                self.response.status = 204
                                self.response.write("Boat docked")
                        #boat already docked
                        else:
                            self.response.status = 403
                            self.response.write("Boat already docked")
                    #no slipID supplied
                    else:
                        self.response.status = 400
                        self.response.write("No slip found to dock at")
            elif 'slipID' in bData:
                if boat.at_sea == False:
                    self.response.status = 403
                    self.response.write("Boat is already docked")
                #boat already at sea
                else:
                    slip = ndb.Key(urlsafe = bData['slipID']).get()
                    if slip == None:
                        self.response.status = 403
                        self.response.write("No slip found")
                    elif slip.current_boat != None:
                        self.response.status = 403
                        self.response.write("Slip is occupied")
                    else:
                        slip.current_boat = boat.key.urlsafe()
                        boat.slipID = slip.key.urlsafe()
                        boat.at_sea = False
                        slip.put()
                        boat.put()
                        self.response.status = 204
                        self.response.write("Boat docked")
            else:
                boat.put()
                self.response.status = 204
                self.response.write("Boat updated")
        else:
            self.response.status = 403
            self.response.write("No boat found")

   def delete(self, id=None):
        if id:
            boat = ndb.Key(urlsafe = id).get()
            if boat:
                slip = None
                if boat.slipID != None:
                    slip = ndb.Key(urlsafe = boat.slipID).get()
                if slip != None:
                    slip.current_boat = None
                    slip.put()
                boat.key.delete()
                self.response.status = 204
                self.response.write("Boat Removed")
            else:
                self.response.status = 403
                self.response.write("No boat found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

class SlipHandler(webapp2.RequestHandler):
   def get(self, id=None):
        if id:
            slip = ndb.Key(urlsafe = id).get()
            if slip:
                slip_dict = slip.to_dict()
                slip_dict['self'] = '/slips/' + id
                slip_dict['id'] = id
                self.response.write(json.dumps(slip_dict, default = dateConverter))
            else:
                self.response.status = 403
                self.response.write("No slip found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

   def put(self, id=None):
        if id:
            slip = ndb.Key(urlsafe = id).get()
            sData = json.loads(self.request.body)
            if 'arrival_date' in sData:
                dateObj = datetime.date.strptime(sData['arrival_date'], '%Y-%m-%d')
                slip.arrival_date = dateObj
            if 'current_boat' in sData:
                boat = ndb.Key(urlsafe = sData['current_boat']).get()
                if boat == None:
                    self.response.status = 403
                    self.response.write("No boat found")
                elif slip.current_boat != None:
                    self.response.status = 403
                    self.response.write("Another boat already docked at slip")
                elif boat.at_sea == False:
                    self.response.status = 403
                    self.response.write("Boat already docked")
                else:
                    slip.current_boat = sData['current_boat']
                    boat.slipID = slip.key.urlsafe()
                    boat.at_sea = False
                    slip.arrival_date = datetime.date.today()
                    slip.put()
                    boat.put()
                    self.response.status = 204
                    self.response.write("Boat docked")
            else:
                self.response.status = 204
                self.response.write("Arrival date updated")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

   def delete(self, id=None):
        if id:
            slip = ndb.Key(urlsafe = id).get()
            if slip:
                boat = ndb.Key(urlsafe = slip.current_boat).get()
                if boat != None:
                    boat.at_sea = True
                    boat.slipID = None
                    boat.put()
                slip.key.delete()
                self.response.status = 204
                self.response.write("Slip Removed")
            else:
                self.response.status = 403
                self.response.write("No slip found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

        
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/slips', Slips),
    ('/slips/(.*)', SlipHandler),
    ('/boats', Boats),
    ('/boats/(.*)', BoatHandler),
], debug=True)

