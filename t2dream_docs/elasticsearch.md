##List indexes

> curl 'localhost:9200/_cat/indices?v'

Output

health status index         pri rep docs.count docs.deleted store.size pri.store.size 

yellow open   encoded         5   1          0            0       575b           575b 

yellow open   annotations     1   1      80275          645     62.3mb         62.3mb 

yellow open   vis_composite   1   1          1            0     37.7kb         37.7kb 

yellow open   snovault        5   1         55            5      5.7mb          5.7mb 
