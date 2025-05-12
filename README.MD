### vpn service with fastapi and etcd as distributed storage

================================================================================
- before install local wireguard
```bash
sudo apt install wireguard
```
- run app with reload
``` bash
sudo chmod +x runner.sh && ./runner.sh
```
- run only etcd
``` bash
./runner.sh -e
```
================================================================================
- for get logs from etcd 
``` bash
docker compose -f local-compose.yml logs -f etcd
```


================================================================================
current issues (TODO):
- [ ] add transactions

================================================================================