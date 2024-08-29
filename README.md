#### How to use?

Set these variables in .bashrc or export them in your favourite terminal app:

for AUTH version 1

```
export ST_AUTH=http://127.0.0.1:8080/auth/v1.0
export ST_USER=test:tester
export ST_KEY=testing
export ST_URL=http://127.0.0.1:8080/v1/AUTH_test

```
all `Domain` variables are id not name

for AUTH version 3 (Project Name)
```
export OS_MONSTER_URL=http://127.0.0.1:8080  
export OS_USERNAME=tester
export OS_PASSWORD=testing
export OS_AUTH_URL="http://127.0.0.1:5000"
export OS_USER_DOMAIN="default"
export OS_PROJECT_NAME="test"
export OS_PROJ_DOMAIN="default"
```

for AUTH version 3 (Project ID)
```
export OS_MONSTER_URL=http://127.0.0.1:8080  
export OS_USERNAME=tester
export OS_PASSWORD=testing
export OS_USER_DOMAIN="default"
export OS_AUTH_URL="http://127.0.0.1:5000"
export OS_PROJECT_ID="test"
```


`apt install pipx`

`pipx install monsterclient`

enjoy :)


##### commands

1. put

```
monster put <container>
monster put <container> <object>
```

2. delete

```
monster delete <container>
monster delete <container> <object>
```

3. get

```
monster get
monster get <container>
monster get <container> <object>
```

4. head

```
monster head
monster head <container>
monster head <container> <object>
```

5. post

```
monster post --header key:value
monster post <container> --header key:value
monster post <container> <object> --header key:value
```

6. info

```
monster info
```

* to see curl command use `-c` or `--curl` option. for example:

```
monster put <container> --curl
```
