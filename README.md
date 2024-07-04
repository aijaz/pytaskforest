Sometimes even though the log file has been removed, a container re-creates it and then the subsequent run of
docker-compose dies because the file was momentarily present.  This is a bug in macos or colima. Using docker desktop works better.


```
# Server:
./startServer.sh

# Client:
docker exec -it pytaskforest-pytf_c-1 /pytf.py status --json  | jq .status.flat_list | less
or ./status.sh
```