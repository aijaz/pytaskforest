
class PyTaskforestParseException(Exception):
    def __init__(self, message="Parse Exception"):
        self.message = message
        super().__init__(self.message)


MSG_INNER_PARSING_FAILED = "Job inner data parsing failed"
MSG_START_TIME_PARSING_FAILED = "Start Time Parsing failed for job:"
