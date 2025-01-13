from datetime import timedelta
import json
import time
import uuid

from pymongo import MongoClient

from spider.utils.math import clamp
from .wrapper import Scheduler
import boto3


class GachigaScheduler(Scheduler):
    def __init__(self, config, *args, **kwargs):
        super(GachigaScheduler, self).__init__(**config['Engine'])
        self._doc_db = MongoClient(**config['DocDB']['args'])
        server_info = self._doc_db.server_info()
        self._base_logger.info("DocDB on AWS Information: {0}".format(server_info))
        
        self.__database = self._doc_db['Pages']
        self._sqs_client = boto3.client(**config['Queue']['args'])
        self._queue = []
        self._config = config
        self.__warm_up_engine()
    
    def step(self):
        return self._engine.run()
    
    # region: Initialization: update root nodes, warm-up engine, etc.
    def __warm_up_engine(self):
        self._base_logger.info("Warm-up engine")
        
        func_kwargs = {'roots': self._config['Roots'], 'collection': self.__database['Roots']}
        self._engine.add_single_event(self.__update_root_nodes, "update root nodes", **func_kwargs)
        self._engine.add_fixed_event(self._check_pending_jobs, "check pending jobs", 3600, collection=self.__database['JobTable'])
        self._engine.add_fixed_event(self._update_job_freshness, "update job freshness", 3600, collection=self.__database['JobTable'])
        self._engine.add_fixed_event(self._adjust_queue_jobs, "update scheduler's queue", 1200)
    
    def __update_root_nodes(self, roots, collection):
        for key, value in roots.items():
            root = {'url': key}
            root.update(value)
            self._update_items(root, collection)
            self.add_request(key, status='inactive', last_updated=time.time() - (30 * 24 * 60 * 60))
    # endregion
    
    # region: Cron jobs: check pending jobs, update job freshness(not recorded)
    def _adjust_queue_jobs(self):
        if len(self._queue) > 0:
            job = self._queue.pop(0)
            self.add_request(**job)
            self._base_logger.info(f"Tried to send a job: {job['url']}")
    
    def _check_pending_jobs(self, collection):
        jobs = collection.find({"status": "pending"}, {"url": 1, "retry": 2, "max_retry": 3})
        
        result_logs = ""
        for job in jobs:
            job['retry'] += 1
            if job['retry'] >= job['max_retry']:
                job['status'] = 'failed'
            
            url = job['url']
            self._base_logger.info(f"Pending job({job['retry']}/{job['max_retry']}): {url}")
            self.add_request(**job)
            result_logs += f"{job['retry']}/{job['max_retry']} | url: {job['url']} \n"
        return result_logs
    
    def _update_job_freshness(self, collection):
        jobs = collection.find({"status": "inactive"}, {"url": 1, "last_updated": 1})
        result_logs = ""
        for job in jobs:
            freshness, gap_hours = self._get_freshness(job['last_updated'], self._config['Roots'][job['url']]['period'])
            if freshness == 1.:
                self.add_request(**job)
            
            self._base_logger.info(f"Job freshness({freshness}): {job['url']}")
            result_logs += f"Freshness: {freshness} | url: {job['url']} \n"
            
        return result_logs

    def _is_available_execution(self, collection) -> bool:
        active_count = collection.count_documents({"status": "active"})
        max_exe_freq = self._config['LifeCycle']['maximum_execution_frequency']
        return active_count <= max_exe_freq
    
    # endregion
    # region: AWS services
    def _invoke_sqs(self, group="crawl", **payload):
        self._base_logger.info("Invoke message to SQS on AWS")
        queue_url = self._config['Queue']['endpoint']
        try:
            response = self._sqs_client.send_message(
                QueueUrl=queue_url,
                MessageGroupId=group,
                MessageDeduplicationId=uuid.uuid1().hex,
                MessageBody=json.dumps(payload)
            )
        except Exception as e:
            self._base_logger.error(e)
            return None
        self._base_logger.info(f"Message ID: {response['MessageId']}")
        return response
    
    def _control_nat(self, del_nat=False, replace_nat=False):
        func_kwargs = {'group': 'nat', 'del_nat_gateway': del_nat, 'replace_nat_gateway': replace_nat}
        length = self._engine.add_single_event(self._invoke_sqs, "invoke_sqs", **func_kwargs)
    
    # endregion
    def _get_freshness(self, last_visited, period):
        gap_hours, _ = divmod(time.time() - last_visited, 3600)
        return clamp(gap_hours / period, 0., 1.), gap_hours
        
    def _update_items(self, job, collection):
        query = {'url': job['url']}      
        contents = {"$set": job}
        doc_id = collection.update_one(query, contents, upsert=True) # insert new job if not exist reason of 'upsert'
        if doc_id.upserted_id:
            self._base_logger.info(f"Added new doc, job ID: {doc_id.upserted_id}")
        return doc_id
    
    def add_request(self, url, **kwargs):
        job = {'url': url, 'status': 'active', 'retry': 0, 'max_retry': 3, 'last_updated': time.time()}
        job.update(kwargs)
        if job['status'] == 'active':
            if self._is_available_execution(self.__database['JobTable']):
                func_kwargs = {'url': url, 'db_ip': self._config['DocDB']['args']['host']}
                length = self._engine.add_single_event(self._invoke_sqs, "invoke_sqs", **func_kwargs)
        
                self._base_logger.info(f"Waited message length: {length}")
            else:
                self._base_logger.info("The message processing for the request failed due to concurrency limits.")
                self._queue.append(job)
                job['status'], job['last_updated'] = 'inactive', time.time()
                self._base_logger.info(f"Queue in Scheduler - length: {len(self._queue)}")
        
        self._update_items(job, self.__database['JobTable'])

    def get_request(self):
        pass

    def task_done(self):
        self._engine.stop()

    def join(self):
        pass

    def empty(self):
        pass