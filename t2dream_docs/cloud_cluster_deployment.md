
## Workflow to deploy database on cloud in cluster mode

This will launch the elastic search and indexing in cluster mode to accomodate large datasets and meet computational demands. Needed for production. The cluster node has only elasticsearch (for indexing & searching) and the master node runs python codebase 

**Deploy to AWS instance:**

Checkout the code on local machine

```
git clone https://github.com/T2DREAM/t2dream-portal.git
```

For production:

Navigate to t2dream-portal local directory and master node

```
bin/deploy --cluster-name vX-cluster --profile-name production --candidate --n vX-master --instance-type c5.9xlarge
```

Launch cluster nodes

```
bin/deploy --elasticsearch yes --cluster-name vX-cluster --cluster-size 3 --profile-name production --name vX-cluster --instance-type c5.xlarge

```

Note: *X is the instance version*

Ensure the --cluster-name for launching cluster nodes and master node is same

Go to AWS console, check cluster nodes and master nodes running

*Important:* Open security groups elasticsearch-https (for elasticsearch cluster mode), ssh-http-https and t2dkp (for REST_API connection) for master and all the cluster nodes individually via. AWS console.

Select public DNS for the master node just deployed, e.g.:
ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com (each time will be different DNS)

Login to master instance to check status of installation:
ssh ubuntu@ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com

View progress:
```
tail -f /var/log/cloud-init-output.log
```

Usually runs without any errors, errors encountered only when modules/dependecies are deprecated

* The master server should automatically reboot after installation is complete
* Going to the URL od master node http://ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com should return the homepage

Login to master node instance to add easticsearch replicas:
ssh ubuntu@ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com


https://www.elastic.co/guide/en/elasticsearch/guide/current/distributed-cluster.html

Add Replicas
```
curl -XPUT 'localhost:9200/_all/_settings' -d '{"index": {"number_of_replicas": 2}}'
```

**Why Replicas and shard??**

**Sharding is important for two primary reasons**
* It allows you to horizontally split/scale your content volume
* It allows you to distribute and parallelize operations across shards (potentially on multiple nodes) thus increasing performance/throughput 

**Replication is important for two primary reasons:**

* It provides high availability in case a shard/node fails. For this reason, it is important to note that a replica shard is never allocated on the same node as the original/primary shard that it was copied from. 
* It allows you to scale out your search volume/throughput since searches can be executed on all replicas in parallel. 


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

* This retrieves the latest wal backups (during installation process) - required for production
https://github.com/T2DREAM/t2dream-portal/blob/master/t2dream_docs/database-backup-retrievals.md#wal-retrivals

* Initiates indexing
Once wal backups are retrived indexing to ES datastore initiates 

* Create and login https://auth0.com/ for authentication and login for autheticated users (AMP consortium members)
1. Create auth0 application (react, application type: single page) 
2. Add the web url to allowed callback urls, allowed web origins and CORS

![](https://github.com/T2DREAM/t2dream-portal/blob/master/t2dream_docs/auth0.png)

3. Enable AWS add on
4. Configure and enable connections for GMAIL(google account), Facebook, Twitter etc. so that user can login using these accounts 
https://auth0.com/docs/dashboard/guides/connections/set-up-connections-social
5. Check if you can login using your social media accounts

* Complete indexing (as of January 2020) takes ~1 hour to index assays, pages, biosamples, annotations and everything else ~30 hours for indexing .bed files for variant search (since indexing of internal hits is slow) 

* Wait for /_indexer snapshot on new instance to match snapshot on old instance (both should be status: "waiting")

On web browser check -  
http://ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com/_indexer

* Attach elastic ip for production server after compelete indexing
* Install security cert on master node https://certbot.eff.org/lets-encrypt/ubuntutrusty-apache
* Size down master c5.9xlarge to c5.4xlarge(not recommended though)

* Create base backup from production machine and schdeule corn jobs to backup postgresdb
https://github.com/T2DREAM/t2dream-portal/blob/master/t2dream_docs/database-backup-retrievals.md#wal-backup

ES best practice 
https://www.elastic.co/guide/en/elasticsearch/reference/current/getting-started.html

https://medium.com/@abhidrona/elasticsearch-deployment-best-practices-d6c1323b25d7

Debuging cluster state and shard allocation
https://www.datadoghq.com/blog/elasticsearch-unassigned-shards/

Reference - https://github.com/ENCODE-DCC/encoded/blob/dev/docs/aws-deployment.rst

Finally online!
