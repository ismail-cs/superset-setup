# superset-setup
setup superset container

after running all 3 (superset, MySQL, redis) container 

enter superset container 
```
docker exec -it superset_container_name bash
```

run this 3 command 

1.
```
superset db upgrade
```

2.
```
superset init
```

3.
```
superset fab create-admin
```
