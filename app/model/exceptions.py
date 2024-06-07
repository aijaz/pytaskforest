
class PyTaskforestParseException(Exception):
    def __init__(self, message="Parse Exception"):
        self.message = message
        super().__init__(self.message)


MSG_INNER_PARSING_FAILED = "Job inner data parsing failed"
MSG_START_TIME_PARSING_FAILED = "Start Time Parsing failed for job:"
MSG_UNTIL_TIME_PARSING_FAILED = "Until Time Parsing failed for job:"
MSG_UNRECOGNIZED_PARAM = "Unrecognized job parameter for job:"
MSG_INVALID_TYPE = "Invalid Type for job/key:"
MSG_FAMILY_START_TIME_PARSING_FAILED = "Start Time Parsing failed for family:"
MSG_FAMILY_UNRECOGNIZED_PARAM = "Unrecognized job parameter for job:"
MSG_FAMILY_FIRST_LINE_PARSE_FAIL = "First line of family failed to parse:"
MSG_FAMILY_INVALID_TYPE = "Invalid Type for job/key:"
MSG_FAMILY_CAL_AND_DAYS = "Cannot have both Calendar and Days specified"
MSG_FAMILY_UNKNOWN_CALENDAR = "Unknown Calendar:"
