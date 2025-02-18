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
        self._nat_client = boto3.client(**config['Nat']['args'])
        self._available_nat_gateway = True
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
        self._engine.add_fixed_event(self._update_job_freshness, "update job freshness", 601, collection=self.__database['JobTable'])
        self._engine.add_fixed_event(self._adjust_queue_jobs, "update scheduler's queue", 30)
        # Must be a last event
        self._engine.add_fixed_event(self._maintain_nat_gateway, "check NAT gateway", 3600, collection=self.__database['JobTable'])
    
    def __update_root_nodes(self, roots, collection):
        for key, value in roots.items():
            root = {'url': key}
            root.update(value)
            self.add_request(key, status='inactive', last_updated=time.time() - (30 * 24 * 60 * 60))
    
    def __update_field(self, field_name, value):
        if hasattr(self, field_name):
            setattr(self, field_name, value)
            self._base_logger.info(f"{field_name} has been updated to {value}.")
        else:
            self._base_logger.info(f"Field '{field_name}' does not exist in the class.")
    # endregion
    
    # region: Cron jobs: check pending jobs, update job freshness(not recorded)
    def _adjust_queue_jobs(self):
        if len(self._queue) > 0:
            job = self._queue.pop(0)
            self.add_request(**job)
            self._base_logger.info(f"Tried to send a job: {job['url']}")
    
    def _check_pending_jobs(self, collection):
        result_logs = ""
        if len(self._queue) > 0:
            self._base_logger.info(f"[PASSED]Exists prioritized jobs: Scheduler's queue length: {len(self._queue)}")
            return result_logs
        jobs = collection.find({"status": "pending"}, {"url": 1, "retry": 2, "max_retry": 3})
        
        for job in jobs:
            job['retry'] += 1
            if job['retry'] >= job['max_retry']:
                job['status'] = 'failed'

            url = job['url']
            self._base_logger.info(f"Pending job({job['retry']}/{job['max_retry']}): {url}")
            self.add_request(**job)
            result_logs += f"{job['retry']}/{job['max_retry']} | url: {job['url']} \n"
        return result_logs
    
    def _set_status(self, collection, url, from_status, to_status):
        result_logs = ""
        jobs = collection.find({"url": url}, {"status": 1, "url": 1})
        
        for job in jobs:
            if from_status != job['status']:
                self._base_logger.info(f"Status can't be changed to {to_status} from {from_status}. current status: {job['status']}-{url}")
                continue
            
            job['status'] = to_status
            self._update_items(job, collection)
            line = f"Changed job status to {to_status}, url: {url}"
            self._base_logger.info(line)
            result_logs += line + '\n'
        return result_logs
    
    def _update_job_freshness(self, collection):
        result_logs = ""
        if len(self._queue) > 0:
            self._base_logger.info(f"[PASSED]Exists prioritized jobs: Scheduler's queue length: {len(self._queue)}")
            return result_logs
        
        jobs = collection.find({"status": "inactive"}, {"url": 1, "last_updated": 1, "retry": 1})
        max_exe_freq = self._config['LifeCycle']['maximum_execution_frequency']
        for job in jobs:
            freshness, gap_hours = self._get_freshness(job['last_updated'], self._config['Roots'][job['url']]['period'])
            self._base_logger.info(f"Job freshness({freshness}): {job['url']}, remain hours: {gap_hours}")
            result_logs += f"Freshness: {freshness} | url: {job['url']} \n"
            
            if freshness == 1. and max_exe_freq > 0:
                max_exe_freq -= 1
                self.add_request(**job)
            
        return result_logs

    def _maintain_nat_gateway(self, collection):
        result_logs = ""
        if not self._is_available_execution(collection):
            return result_logs
        
        jobs = list(collection.find({}, {'url': 1, 'status': 1, 'last_updated': 1}))
        failed_jobs = []
        min_remain_hours = 240
        
        for job in jobs:
            if job['status'] in ["active", "pending"]:
                self._base_logger.info("Not a condition manage NAT gateway reason of active job(s).")
                return
            
            elif job['status'] == "failed":
                failed_jobs.append(job)
            
            _, gap_hours = self._get_freshness(job['last_updated'], self._config['Roots'][job['url']]['period'])
            if min_remain_hours > gap_hours:
                min_remain_hours = gap_hours
        
        if min_remain_hours > 2.:
            self._base_logger.info(f"Remain hours: {min_remain_hours}, Tried to delete NAT gateway.") 
            self._control_nat(del_nat=True)
            for job in failed_jobs:
                job = {'url': job['url'], 'status': 'inactive', 'retry': 0, 'max_retry': 3, 'last_updated': time.time()}
                self._update_items(job, collection)
        
        else:
            if not self._available_nat_gateway:
                self._base_logger.info("Tried to replace NAT gateway.")
                self._control_nat(replace_nat=True)
        
        return result_logs
    
    def _is_available_execution(self, collection) -> bool:
        if len(self._queue) > 0:
            active_count = len(self._queue)
        else:
            active_count = collection.count_documents({"status": "active"})
            
        max_exe_freq = self._config['LifeCycle']['maximum_execution_frequency']
        return active_count < max_exe_freq
    
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
    
    def _invoke_nat(self, **payload):
        arn = self._config['Nat']['endpoint']
        try:
            response = self._nat_client.start_execution(
                stateMachineArn=arn,
                input=json.dumps(payload)
            )
            self._base_logger.info(f"Execution Stepfunctions: {response['executionArn']}")
            return response['executionArn']
        
        except Exception as e:
            self._base_logger.error(e)
            return None
    
    def _control_nat(self, del_nat=False, replace_nat=False):
        if self._available_nat_gateway == False and del_nat == True:
            self._base_logger.info("[PASSED] Already deleted NAT gateway")
            return

        func_kwargs = {'del_nat_gateway': del_nat, 'replace_nat_gateway': replace_nat}
        _ = self._engine.add_single_event(self._invoke_nat, "invoke_sqs", **func_kwargs)
        
        _ = self._engine.add_single_event(self.__update_field, "reset_nat_gateway_status",
                                          **{'field_name': '_available_nat_gateway', 'value': False})
        if replace_nat:
            # It takes about 3 mins
            length = self._engine.add_single_event(self.__update_field, "update_nat_gateway_status",
                                                delay=60 * 5, **{'field_name': '_available_nat_gateway', 'value': True})
    
    # endregion
    # region: Utilities and Override functions
    def _get_freshness(self, last_visited, period):
        gap_hours, _ = divmod(time.time() - last_visited, 3600)
        return clamp(gap_hours / period, 0., 1.), period - gap_hours
        
    def _update_items(self, job, collection):
        query = {'url': job['url']}      
        contents = {"$set": job}
        doc_id = collection.update_one(query, contents, upsert=True) # insert new job if not exist reason of 'upsert'
        if doc_id.upserted_id:
            self._base_logger.info(f"Added new doc, job ID: {doc_id.upserted_id}")
        return doc_id
    
    def add_request(self, url, **kwargs):
        if self._available_nat_gateway == False:
            self._base_logger.error("No NAT Gateway!! Can't do any process. Revive network configurations.")
            return
        
        job = {'url': url, 'status': 'active', 'retry': 0, 'max_retry': 3, 'last_updated': time.time()}
        job.update(kwargs)
        if job['status'] == 'active':
            if self._is_available_execution(self.__database['JobTable']):
                invoke_kwargs = {'url': url, 'db_ip': self._config['DocDB']['args']['host']}
                status_kwargs = {'url': url, 'from_status': 'active', 'to_status': 'pending', 'collection': self.__database['JobTable']}
                job['last_updated'] = time.time()
                length = self._engine.add_single_event(self._invoke_sqs, "invoke_sqs", **invoke_kwargs)
                length = self._engine.add_single_event(self._set_status, "time_out_timer", delay=self._config['Queue']['timeout'], **status_kwargs)
                
                self._base_logger.info(f"Waited message length: {length}")
            else:
                self._base_logger.info("The message processing for the request failed due to concurrency limits.")
                self._queue.append(job)
                job['status'] = 'inactive'
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
    # endregion