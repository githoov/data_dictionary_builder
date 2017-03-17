import os, glob
import json
import getpass
import looker_python as looker


class Looker(object):

  def __init__(self, url, model):
    """
    For the most part, we will almost always want url = 'https://<path>.looker.com:19999/api/3.0'; 
    however, that may change in the future. Making this a more generalizable initialiation.
    """
    self.id     = getpass.getpass(prompt = 'API ID: ')
    self.secret = getpass.getpass(prompt = 'API Secret: ')
    self.url    = url
    self.model  = model

  def __dict_subset__(self, field_array, key_subset):
    a = []
    for i in field_array:
      element = {k: i[k] for k in key_subset}
      a.append(element)
    return a

  def connect(self):
    unauthenticated_client  = looker.ApiClient(self.url)
    unauthenticated_authApi = looker.ApiAuthApi(unauthenticated_client)
    token                   = unauthenticated_authApi.login(client_id = self.id, client_secret = self.secret)
    self.client             = looker.ApiClient(self.url, 'Authorization', 'token ' + token.access_token)

  def metadata_api(self):
    self.metadata = looker.LookmlModelApi(self.client)

  def get_explore_data(self):
    print("Gathering explore metadata...")
    self.model_metadata   = self.metadata.lookml_model(lookml_model_name = self.model)
    self.explores         = [i['name'] for i in self.model_metadata.to_dict()['explores']]
    print("Success! You can access explore metadata in the Looker class variable `explores`.")

  def get_view_data(self, explore, interesting_keys):
    print("Gathering metadata about %s..." % explore)
    explore_data = self.metadata.lookml_model_explore(lookml_model_name = self.model, explore_name = explore)
    view_data    = [i for i in explore_data.to_dict()['fields']['dimensions'] if i['view'] == explore]
    return self.__dict_subset__(view_data, interesting_keys)


class Generator(object):

  def __init__(self, path):
    self.path = path

  def create_header_rst(self, field_data):
    return "``%s``\n==================================================================================================\n\n" % field_data or "unknown"

  def create_field_rst(self, field_data):
    name        = field_data['name'].split('.')[1] or field_data['name']
    label_short = field_data['label_short']
    description = field_data['description']
    data_type   = field_data['type']
    sql         = (field_data['sql'] or 'N/A').strip().replace('\n', '')
    rst         = "``%s``\n\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\n- **Alias**: %s\n- **Description**: %s\n- **Data Type**: ``%s``\n- **Definition**: ``%s``\n\n" % (name, label_short, description, data_type, sql)
    return rst

  def generate_file(self, data):
    print("Creating file for %s..." % data['view'])
    path = "%s/%s.rst" % (self.path, data['view'])
    with open(path, "a") as file:
      file.write(self.create_header_rst(data['view']))
      for field in data['fields']:
        file.write(self.create_field_rst(field))

  def generate_index(self, explore_list):
    print("Creating index file")
    path  = "%s%s.rst" % (self.path, '/index')
    views = '\t\n'.join(explore_list)
    index = "Welcome to the Data Dictionary!\n===================================================\nThis page provides descriptions for all of the fields in Looker and Snowhouse as well as their SQL or LookML definitions.\n\nThe documentation is broken out at the entity level (*i.e.*, the Snowhouse-table or Looker-view level, if you prefer to think of it that way).\n\nUnder each entity, one can browse the name of the fields, their aliases or pretty names, a description for each field, and finally the SQL or LookML definition for each field.\n\nEntities:\n==================\n\n.. toctree::\n\
  :titlesonly:\n\
  :maxdepth: 1\n\n\t\t\
  %s\n\nIndices and tables\n==================\n\n\t* :ref:`search` \n" % views

    with open(path, "a") as file:
      file.write(index)

def main():
  filelist = glob.glob("*.rst")
  for f in filelist:
      os.remove(f)
  interesting_keys = ('name', 'description', 'label_short', 'sql', 'type')
  lkr = Looker(url = 'https://<path>.looker.com:19999/api/3.0', model = '<your_model>')
  lkr.connect()
  lkr.metadata_api()
  lkr.get_explore_data()
  field_data = []
  for i in lkr.explores:
    field_data.append({'view': i, 'fields': lkr.get_view_data(i, interesting_keys)})
  gen = Generator('~/looker_documentation')
  for view in field_data:
    gen.generate_file(view)
  gen.generate_index(lkr.explores)

if __name__ == '__main__':
  main()