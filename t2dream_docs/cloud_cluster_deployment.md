
## Workflow to deploy database on cloud in cluster mode

This will launch the elastic search and indexing in cluster mode to accomodate large datasets and meet computational demands. Needed for production and upload (demo) machines. The cluster node has only elasticsearch (for indexing & searching) and the master node runs python codebase 

**Deploy to AWS instance:**

Checkout the code on local machine

```
git clone https://github.com/T2DREAM/t2dream-portal.git
```

For production:

Navigate to t2dream-portal local directory and launch cluster nodes

```
bin/deploy --elasticsearch yes --cluster-name vX-cluster --cluster-size 4 --profile-name production --name vX-cluster --instance-type m4.xlarge
```

Launch cluster nodes

```
bin/deploy --cluster-name vX-cluster --profile-name production --candidate --n vX-master --instance-type c4.8xlarge
```

Note: *X is the instance version*

Go to AWS console, check cluster nodes and master nodes running

Select public DNS for the master node just deployed, e.g.:
ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com (each time will be different DNS)

Login to instance to check status of installation:
ssh ubuntu@ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com

https://www.elastic.co/guide/en/elasticsearch/guide/current/distributed-cluster.html

View cluster health on master
```
curl localhost:9200/_cluster/health?pretty
```

```
{
  "cluster_name" : "v6-cluster",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 5,
  "number_of_data_nodes" : 4,
  "active_primary_shards" : 102,
  "active_shards" : 204,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0
}
```

On cluster instance
```
{
  "cluster_name" : "v6-cluster",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 5,
  "number_of_data_nodes" : 4,
  "active_primary_shards" : 102,
  "active_shards" : 204,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0
}
```

Note: *Security groups elasticsearch-https and ssh-http-https should open for the cluser instances*

View progress:
```
tail -f /var/log/cloud-init-output.log
```

Usually runs without any errors, errors encountered only when modules/dependecies are deprecated

* The master server should automatically reboot after installation is complete
* Going to the URL http://ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com should return the homepage
* This retrieves the latest wal backups (during installation process) - required for demo and production
* Initiates indexing

Check logs on master

```
tail /var/log/apache2/error.logs
```

check indexing on cluster nodes
```
sudo tail /var/log/elasticsearch/v6-cluster_index_indexing_slowlog.log
```

* Complete indexing (as of May 18th 2018) takes ~ hours (while indexing is in-progress check logs for errors)
* Attach elastic ip for demo (data upload server) and production server after compelete indexing
* Install security cert https://certbot.eff.org/lets-encrypt/ubuntutrusty-apache
* Size down master c2.8xlarge to c2.4xlarge(not recommended though)
* For Demo create and schedule wal backups (at 6pm daily)

https://github.com/T2DREAM/t2dream-portal/blob/master/t2dream_docs/database-backup-retrievals.md

Debuging cluster state and shard allocation
https://www.datadoghq.com/blog/elasticsearch-unassigned-shards/

Reference - https://github.com/ENCODE-DCC/encoded/blob/dev/docs/aws-deployment.rst

Finally online!
