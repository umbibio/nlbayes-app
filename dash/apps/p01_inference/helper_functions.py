import os
import io
import json
import base64
from datetime import datetime
from hashlib import sha256
from glob import glob

import pandas as pd

import gridfs
from pymongo import MongoClient
from bson.objectid import ObjectId
from celery import Celery
import celery


broker = os.environ['NLB_QUEUE_BROKER']
backend = os.environ['NLB_QUEUE_BACKEND']
mongo_url = os.environ['NLB_DATA_STORE']
worker = Celery('nlbayes_jobs', backend=backend, broker=broker)


def parse_contents(contents:str, filename: str):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if filename.lower().endswith('.csv'):
            content = decoded.decode('utf-8')
            if content.count(',') == 0:
                # check if it is a tsv instead
                if content.count('\t') > 0:
                    sep = '\t'
            else:
                sep = ','
            # Assume that the user uploaded a CSV file
            return pd.read_csv(io.StringIO(content), sep=sep)

        elif filename.lower().endswith('.tsv'):
            content = decoded.decode('utf-8')
            if content.count('\t') == 0:
                # check if it is a csv instead
                if content.count(',') > 0:
                    sep = ','
            else:
                sep = '\t'
            # Assume that the user uploaded a TSV file
            return pd.read_csv(io.StringIO(content), sep=sep)

        elif filename.lower().endswith('.xlsx') or filename.lower().endswith('.xls'):
            # Assume that the user uploaded an excel file
            return pd.read_excel(io.BytesIO(decoded))

        elif filename.lower().endswith('.json'):
            return json.loads(decoded)

    except Exception as e:
        print(e, flush=True)
        return None
    
    print("No matching extension")
    return None


class NLBayesFS:
    def __init__(self, mongo_client) -> None:
        gfs_db = mongo_client.nlbayes_gfs_db
        self.gfs = gridfs.GridFS(gfs_db)

    def save_file(self, filebytes, filename):
        hash = sha256(filebytes).hexdigest()

        if not self.gfs.exists(_id=hash):
            self.gfs.put(filebytes, _id=hash, filename=filename)
        else:
            file = self.gfs.find_one({'_id': hash})
            if filename != file.filename:
                raise ValueError('filename is different')

        return hash

    def load_file(self, hash):

        file = self.gfs.find_one({'_id': hash})
        return file.read(), file.filename


DEFAULT_CONFIG = { 'uniform_t': False, 't_alpha': None, 't_beta': None,
                   'zy': 0.99, 'zn': 0., 's_leniency': 0.1}

def submit_job(network, evidence, config=DEFAULT_CONFIG):

    mongo_client = MongoClient(mongo_url)
    jobs = mongo_client.nlbayes_job_db.jobs
    fs = NLBayesFS(mongo_client)

    network_b = json.dumps(network).encode()
    network_hash = fs.save_file(network_b, 'network.json')

    evidence_b = json.dumps(evidence).encode()
    evidence_hash = fs.save_file(evidence_b, 'evidence.json')

    data = { 'network_hash': network_hash,
             'evidence_hash': evidence_hash,
             'config' : config,
             'submit_time': datetime.now().isoformat(), }

    job_id = str(jobs.insert_one(data).inserted_id)
    task_id = worker.send_task('ornor_inference', kwargs={'job_id': job_id}).task_id

    print('job object created:', job_id, flush=True)
    print(f"{task_id=}", flush=True)

    mongo_client.close()
    return job_id, task_id, data


def get_job_status(task_id):
    res = worker.AsyncResult(task_id, task_name='ornor_inference')
    return res._get_task_meta()


def load_json_file(posterior_hash):
    mongo_client = MongoClient(mongo_url)
    fs = NLBayesFS(mongo_client)
    content, filename = fs.load_file(posterior_hash)
    assert filename.endswith('.json')

    return json.loads(content)

