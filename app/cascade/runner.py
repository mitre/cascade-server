# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import datetime
import logging
import traceback

from app import async_wrapper
from app.cascade.jobs import Job


logger = logging.getLogger(__name__)
running_jobs = 0


def run(debug=False):

    # TODO: configuration here
    query_frequency = 1  # seconds between each job check

    jobs_run = []

    def worker():
        jobs_to_run = Job.objects(status=Job.READY)
        count = jobs_to_run.count()
        if count:
            logger.debug("worker call: %d jobs to run" % count)
        else:
            return False

        @async_wrapper.async_routine
        def async_handle_job(j):
            global running_jobs

            j.update(status=Job.STARTED, message=None, count=0, results=[], events=[])

            running_jobs += 1
            logger.debug("handling {} {}".format(type(j).__name__, j.id))
            try:
                j.run()
                logger.debug("success job \"%s\"----" % j.id)
                j.status = Job.SUCCESS
            except Exception as e:
                traceback.print_exc()
                j.message = "{}: {}".format(type(e).__name__, e.message if e.message else e)
                j.status = Job.FAILURE
            finally:
                j.save()

        for job in jobs_to_run:
            if job.user is not None:
                logger.debug("dispatching job \"%s\" ----" % job.id)
                job.update(status=Job.DISPATCHED)
                # will spawn a greenlet in the background
                async_handle_job(job)
            else:
                job.delete()

        return True

    logger.info("Resetting all dispatched events")
    # reclaim dispatched jobs that have not been started
    # useful for when restarting the job runner if it
    Job.objects(status=Job.DISPATCHED).update(status=Job.READY, updated=datetime.datetime.utcnow())
    # reset all started events too
    Job.objects(status=Job.STARTED).update(status=Job.READY, updated=datetime.datetime.utcnow())
    logger.info("Waiting for worker events...")

    while True:
        if worker():
            logger.info("Completed all jobs. Waiting for new jobs to be submitted...")
        async_wrapper.sleep(query_frequency)




