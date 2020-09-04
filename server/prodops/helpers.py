from dash.features.reports import reports


def reprocess_report_job(job_id):
    original_job = reports.ReportJob.objects.get(pk=job_id)

    new_job = reports.ReportJob(user=original_job.user, query=original_job.query)
    new_job.save()
    reports.ReportJobExecutor(new_job).execute()
    return new_job


def reprocess_report_job_async(job_id, **kwargs):
    original_job = reports.ReportJob.objects.get(pk=job_id)

    new_job = reports.ReportJob(user=original_job.user, query=original_job.query)
    new_job.save()

    reports.execute.delay(new_job.id, **kwargs)
    return new_job


def reprocess_report_jobs_async(job_ids, reprocess_title_prefix, reprocess_reason):
    new_jobs = []
    for jid in job_ids:
        new_job = reprocess_report_job_async(
            jid, reprocess_title_prefix=reprocess_title_prefix, reprocess_reason=reprocess_reason
        )
        new_jobs.append(new_job)
    return new_jobs
