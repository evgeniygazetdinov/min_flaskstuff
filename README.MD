### vpn service with fastapi and etcd as distributed storage
```bash
docker compose -f docker-compose.prod.yml up -d
``` 
- for get logs from etcd 
``` bash
docker compose -f local-compose.yml logs -f etcd
```

- run app with reload
``` bash
sudo chmod +x runner.sh && ./runner.sh
```
- run only etcd
``` bash
./runner.sh -e


- [] add transactions