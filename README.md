Sometimes even though the log file has been removed, a container re-creates it and then the subsequent run of
docker-compose dies because the file was momentarily present. Thats why I always create the log file before 
starting docker-compose. I think this is a bug in macos or colima.

```
# Server:
./startServer.sh

# Client:
docker exec -it pytaskforest-pytf_c-1 /pytf.py status | jq .status.flat_list | less
```