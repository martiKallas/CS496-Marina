import webapp2
import json
from google.appengine.ext import ndb

##########       OBJECTS     ########## 
class Slip(ndb.Model):
    #TODO: Add ID
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date = ndb.DateProperty()
    #optional : departure history (list)

class Boat(ndb.Model):
    #TODO: make name unique
    name = ndb.StringProperty()
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
        outString = "{"
        for slip in qry:
            slip_dict = slip.to_dict()
            slip_dict['self'] = '/slips/' + slip.key.urlsafe()
            slip_dict['id'] = slip.key.urlsafe()
            outString = outString + json.dumps(slip_dict) + ','
        if qry.get():
            outString = outString[:-1]
        outString = outString + '}'
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(outString)


    def post(self):
        #TODO: check if slip number already exists
        sData = json.loads(self.request.body)
        new_slip = Slip(number=sData['number'], current_boat=None, arrival_date=None)
        new_slip.at_sea = True 
        new_slip.put()
        slip_dict = new_slip.to_dict()
        slip_dict['self'] = '/slips/' + new_slip.key.urlsafe()
        slip_dict['id'] = new_slip.key.urlsafe()
        self.response.write(json.dumps(slip_dict))

class Boats(webapp2.RequestHandler):
    def get(self):
        #source: https://cloud.google.com/appengine/docs/standard/python/ndb/queryclass
        qry = Boat.query()
        outString = "{"
        for boat in qry:
            boat_dict = boat.to_dict()
            boat_dict['self'] = '/boats/' + boat.key.urlsafe()
            boat_dict['id'] = boat.key.urlsafe()
            boat_dict['slip'] = None
            if boat.slipID:
                slip = ndb.Key(urlsafe = boat.slipID).get()
                boat_dict['slip'] = '/slips/' + slip.key.urlsafe()
            outString = outString + json.dumps(boat_dict) + ','
        if qry.get():
            outString = outString[:-1]
        outString = outString + '}'
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(outString)

    def post(self):
        #TODO: check if boat name already exists
        bData = json.loads(self.request.body)
        new_boat = Boat(name=bData['name'], type=bData['type'], length=bData['length'])
        new_boat.at_sea = True 
        new_boat.slipID = None
        new_boat.put()
        boat_dict = new_boat.to_dict()
        boat_dict['self'] = '/boats/' + new_boat.key.urlsafe()
        boat_dict['id'] = new_boat.key.urlsafe()
        self.response.write(json.dumps(boat_dict))

class BoatHandler(webapp2.RequestHandler):
   def get(self, id=None):
        if id:
            boat = ndb.Key(urlsafe = id).get()
            #TODO: this next line may not work - check it out
            if boat:
                boat_dict = boat.to_dict()
                boat_dict['self'] = '/boats/' + id
                boat_dict['id'] = id
                self.response.write(json.dumps(boat_dict))
            else:
                #TODO: adjust response code
                self.response.write("No boat found")
        else:
            #TODO: adjust response code
            self.response.write("No boat found")

   def patch(self, id=None):
        if id:
            boat = ndb.key(urlsafe = id).get()
            #TODO: do we want to add Ops to this request? - for update and dock?
            bData = json.loads(self.request.body)
        else:
            #TODO: change response status
            self.response.write("No boat found")

   def delete(self, id=None):
        if id:
            boat = ndb.Key(urlsafe = id).delete()
            if boat:
                #TODO: change response status
                self.response.write("Boat Removed")
            else:
                self.reesponse.write("No boat found")
        else:
            #TODO: adjust response code
            self.response.write("No boat found")

class SlipHandler(webapp2.RequestHandler):
   def get(self, id=None):
        if id:
            slip = ndb.Key(urlsafe = id).get()
            if slip:
                slip_dict = slip.to_dict()
                slip_dict['self'] = '/slips/' + id
                slip_dict['id'] = id
                self.response.write(json.dumps(slip_dict))
            else:
                self.response.write("No slip found")
        else:
            #TODO: adjust response code
            self.response.write("No slip found")

   def delete(self, id=None):
        if id:
            slip = ndb.Key(urlsafe = id).delete()
            if slip:
                #TODO: change response status
                self.response.write("Slip Removed")
            else:
                self.response.write("No slip found")
        else:
            #TODO: adjust response code
            self.response.write("No slip found")

        
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/slips', Slips),
    ('/slips/(.*)', SlipHandler),
    ('/boats', Boats),
    ('/boats/(.*)', BoatHandler),
], debug=True)

