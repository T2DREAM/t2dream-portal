
## Issues and how to fix them

**Reindexing**

curl -XDELETE 'http://localhost:9200/snovault' (**Beware** This deletes entire index)

Restart the server/apache

Run mapping script
```
sudo -u encoded bin/create-mapping production.ini --app-name app
```

