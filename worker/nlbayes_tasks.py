import json
from datetime import datetime
from hashlib import sha256
import os
import socket

broker = os.environ['NLB_QUEUE_BROKER']
backend = os.environ['NLB_QUEUE_BACKEND']
mongo_url = os.environ['NLB_DATA_STORE']

from celery import Celery
from pymongo import MongoClient
import gridfs
from bson.objectid import ObjectId

from nlbayes import ModelORNOR


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
        return file.read()


worker = Celery('nlbayes_jobs', backend=backend, broker=broker)
@worker.task(bind=True, name="ornor_inference")
def taskModelORNOR(self, job_id):
    mongo_client = MongoClient(mongo_url)
    jobs = mongo_client.nlbayes_job_db.jobs
    fs = NLBayesFS(mongo_client)

    query = {'_id': ObjectId(job_id)}
    job = jobs.find_one(query)

    network_hash = job['network_hash']
    evidence_hash = job['evidence_hash']
    config = job['config']

    network = json.loads(fs.load_file(network_hash))
    evidence = json.loads(fs.load_file(evidence_hash))
    model = ModelORNOR(network, evidence, **config)

    start_time = datetime.now()
    meta = { 'job_id': job_id,
             'worker_id': socket.gethostname(),
             'start_time': start_time.isoformat(), }
    jobs.update_one(query, {"$set": {'meta': meta}}, upsert=False)

    converged = False
    self.update_state(state="BURNIN", meta=meta)
    while not converged:
        status = model.sample_n(20, 5, 5.0, False, True)
        converged = status == 0

        current_time = datetime.now()
        elapsed_time = current_time - start_time
        progress = { 'n_sampled': model.total_sampled,
                     'gr_stat': model.get_max_gelman_rubin(), 
                     'elapsed_time': str(elapsed_time), }
        meta.update(progress)
        self.update_state(state="BURNIN", meta=meta)

    model.burn_stats()

    N = 10000
    converged = False
    self.update_state(state="SAMPLING", meta=meta)
    while model.total_sampled < N and not converged:
        n = min(20, N - model.total_sampled)
        status = model.sample_n(n, 5, 1.15, False, True)
        converged = status == 0

        current_time = datetime.now()
        elapsed_time = current_time - start_time
        progress = { 'n_sampled': model.total_sampled,
                     'gr_stat': model.get_max_gelman_rubin(),
                     'elapsed_time': str(elapsed_time), }
        meta.update(progress)
        self.update_state(state="SAMPLING", meta=meta)

    meta.update({'end_time': current_time.isoformat()})
    self.update_state(state="COMPLETE", meta=meta)

    posterior = { 'X': model.get_posterior_mean_stat('X', 1),
                  'T': model.get_posterior_mean_stat('T', 0), }
    posterior_b = json.dumps(posterior).encode()
    posterior_hash = fs.save_file(posterior_b, 'posterior.json')

    data = { 'meta': meta,
             'posterior_hash': posterior_hash, }
    jobs.update_one(query, {"$set": data}, upsert=False)

    mongo_client.close()

    return data
