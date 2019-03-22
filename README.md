# docker-secret-hash
Use hash tokens in docker compose secret names to get around immutable docker secret limitations.

TODO: I need to clean up this repo.

## Example

### Setup

```sh
# put secrets in a temporary location for this example
cp -r test/secrets/ /tmp/secrets

# build the secret hasher image
docker-compose -f docker-compose-test.yml build
```

### Deploy Service

```sh
# use the secret hasher container to create some variables to export
docker-compose -f docker-compose-test.yml run parse >  ./output/secret-tags
# take a look at the variables, for kicks (*)
cat ./output/secret-tags
# export the variables. this syntax is linux-only. what's a cross-platform way to do the same?
export $(grep -v '^#' ./output/secret-tags | xargs)
# interpolate variables in the target compose file with the new secret names and deploy the stack
docker-compose -f ./test/input/short.yml config 2>/dev/null | docker stack deploy -c- mystack
# for kicks, take a look at the rendered compose configuration that was used above
docker-compose -f ./test/input/short.yml config

# remove orphaned secrets
docker secret rm $(docker secret ls -q) 2> /dev/null || true
```

### Test

```sh
# get the service's container id
container_id=$(for f in $(docker service ps -q mystack_nginx);do docker inspect --format '{{.Status.ContainerStatus.ContainerID}}' $f; break; done)
# show one of the secrets from within the service's container
docker exec -it $container_id cat /run/secrets/aws_inbound_path
```

### Secret Value Change Test

```sh
# change a secret's value
echo "oh no, i'm a new secret value" > /tmp/secrets/aws_inbound_path
```

Now, repeat the "Deploy Service" and "Test" steps, and you should see the test return the new secret value.

## Notes

\* The generated `./output/secret-tags` looks like the following.
```ini
# aws_inbound_path /tmp/secrets/aws_inbound_path
SECRET_SUM_aws_inbound_path=5ce25192496704043f42c835aaf6e61e
# cfml_app_secrets /tmp/secrets/credentials.properties
SECRET_SUM_cfml_app_secrets=d00d41c9779437670b6c2d098bd7f9e3
```

The `export` command in the example (the one that's currently linux-only) ends up doing this:
```sh
export SECRET_SUM_aws_inbound_path=5ce25192496704043f42c835aaf6e61e
export SECRET_SUM_cfml_app_secrets=d00d41c9779437670b6c2d098bd7f9e3
```
...which makes those variables ready for the `docker-compose ... config` command that follows.
