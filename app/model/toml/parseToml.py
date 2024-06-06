from tomlkit import parse
import json

tomlstr = """
family = { start = '02:00', tz = 'GMT',days = ['Mon', 'Wed', 'Fri'] }
"""

doc = parse(tomlstr)
print(json.dumps(doc))

tomlstr = """
family = { start = '02:00', tz = 'GMT',days = ['Mon', 'Wed', 'Fri'] }

[[job-lines]]
[[job-lines.jobs]]
job_name = "J_ROTATE_LOGS"

[[job-lines]]
[[job-lines.jobs]]
job_name = "J_RESOLVE_DNS"
[[job-lines.jobs]]
job_name = "Delete_Old_Logs"

[[job-lines]]
[[job-lines.jobs]]
job_name = "J_WEB_REPORTS"

[[job-lines]]
[[job-lines.jobs]]
job_name = "J_EMAIL_WEB_RPT_DONE"

"""

doc = parse(tomlstr)
print(json.dumps(doc, indent=2))

