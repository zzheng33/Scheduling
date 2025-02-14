import sys

# Import packages external to pbs, required for redis import
sys.path.append('/usr/local/lib/python3.8/dist-packages')
import pbs
import os
import time
import redis
e = pbs.event()
try:
    r = redis.StrictRedis(host='head.testbed_zz.schedulingpower.emulab.net', port=6379, decode_responses=True)
    # Information to collect 
    event_type = ''
    event_code = e.type
    job_name = e.job.Job_Name

    # Find the event type
    if e.type is pbs.QUEUEJOB:

        event_type = 'q'
        # Job ids - Using counter from Redis
        if r.exists('job_counter'):
            job_counter = r.incr('job_counter')
            job_name = f'job.{job_counter}'
        else:
            # Key doesn't exist, create and initialize it to 0
            r.set('job_counter', 0)
            job_name = 'job.0'
        pbs.event().job.Job_Name = job_name

    elif e.type == pbs.RUNJOB:
        event_type = 'r'
    elif e.type == pbs.EXECJOB_BEGIN:
        event_type = 'mom_r'
    elif e.type == pbs.EXECJOB_END:
        event_type = 'mom_e'
    else:
        event_type = 'unknown'

    # Insert data into redis stream
    r.xadd(
        "redis-hook",
        { "job_id": f"{job_name}", "event_type": event_type, "event_code": event_code},
    )

    # accept the event
    pbs.event().accept() 
except SystemExit:
    pass 
except:
    pbs.event().reject_msg = f'{e.hook_name} hook failed with {sys.exc_info()[:2]}'
    pbs.event().reject("%s hook failed with %s. Please contact Admin" % (pbs.event().hook_name, sys.exc_info()[:2]))
