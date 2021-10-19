class FileReader():
    def __init__(self, train_times, crew_times):
        self.in_file_train = open(train_times, 'r')
        self.in_file_crew = open(crew_times, 'r')
        self.train_times = []
        self.crew_times = []
        self.unloading_times = []
        self.new_crew_times = []

    def _read_train_file(self):
        for line in self.in_file_train:
            try:
                train, unload, crew = line.split(' ')
                self.train_times.append(float(train))
                self.unloading_times.append(float(unload))
                self.crew_times.append(float(crew))
            except:
                self.in_file_train.close()
                return False
            break
        return True

    def get_next_train(self):
        if len(self.train_times)> 0:
            return self.train_times.pop(0)
        else:
            if self._read_train_file():
                return self.get_next_train()
            else:
                return None

    def get_next_unload(self):
        if len(self.unload_times)> 0:
            return self.unload_times.pop(0)
        else:
            if self._read_train_file():
                return self.get_next_unload()
            else:
                return None

    def get_next_crew(self):
        if len(self.crew_times)> 0:
            return self.crew_times.pop(0)
        else:
            if self._read_train_file():
                return self.get_next_crew()
            else:
                return None

    def get_next_crew_arrive(self):
        if len(self.new_crew_times)> 0:
            return self.new_crew_times.pop(0)
        else:
            for line in self.in_file_crew:
                new_crew_time = line.split(' ')[0]
                self.new_crew_times.append(float(new_crew_time))
                break
            return self.get_next_crew_arrive()