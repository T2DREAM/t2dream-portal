##TBD to maximize indexing and search of ES datastore

Queue size
'''
curl -XPUT 'localhost:9200/_all/_settings' -d 
{
  "persistent" : {
    "threadpool" : {
      "index" : {
        "queue_size" : "1000"
      },
      "search" : {
        "queue_size" : "400"
      }
    }
  },
  "transient" : { }
}
'''

Replicas
'''
curl -XPUT 'localhost:9200/_all/_settings' -d '{"index": {"number_of_replicas": 2}}'
'''
