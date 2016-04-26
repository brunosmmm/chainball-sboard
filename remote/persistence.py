import json

class RemotePersistence(object):

    def __init__(self, persistence_file):

        self.pfile = persistence_file

        try:
            with open(persistence_file, 'r') as f:
                self.remote_list = json.load(f)
        except:
            self.remote_list = {}

    def _do_save(self):
        with open(self.pfile, 'w') as f:
            json.dump(self.remote_list, f)

    def is_known(self, remote_id):
        return hex(remote_id) in self.remote_list

    def add_remote(self, remote_id, data=None):
        self.remote_list[hex(remote_id)] = data
        self._do_save()

    def upd_data(self, remote_id, data):
        self.remote_list[hex(remote_id)] = data
        self._do_save()

    def get_remote_persist(self):
        return self.remote_list

PERSISTENT_REMOTE_DATA = RemotePersistence('data/persist/remote.json')
