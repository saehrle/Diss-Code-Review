import pandas as pd
LOG_FILE = 'thesaurusMaker_logfile.txt'

class ToDosLogger:
    def __init__(self, log_file):
        self.logs_list = pd.DataFrame(columns=['ErrorType', 'warnInfoError','Message'])
        self.log_file = log_file

    def addToLogger(self,error_type, warnInfoErr, message):
        file = open(self.log_file, "a+") # will not overwrite old logfile but rather append
        print("Added to Logger (" + warnInfoErr + "): [" + error_type + "] " + message)
        file.write(error_type + "," + warnInfoErr + "," + message + "\n")
        file.flush()
        file.close()

    def sortLoggerOutput(self):
        self.logs_list.sort_values("ErrorType",inplace=True)
        log_file_name = self.log_file.split(".")[0]
        self.logs_list.to_csv(log_file_name + ".csv", index=False, header=False)
        print("\n\nSorted the logger output and wrote to file.\n")

    def makeLogTable(self,error_type):
        self.logs_list.sort_values("warnInfoError")
        subtable = self.logs_list[self.logs_list["ErrorType"] == error_type]
        print("\n\nThis is the list of logs for " + error_type.upper() + "\n---")
        print(subtable)

    def printLogs(self):
        self.logs_list = pd.read_csv(self.log_file,
            names=['ErrorType', 'warnInfoError','Message'])
        existing_error_types = self.logs_list["ErrorType"].unique().tolist()
        for error_type in existing_error_types:
            self.makeLogTable(error_type)
        self.sortLoggerOutput()
