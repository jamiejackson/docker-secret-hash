# docker-secret-hash
Use hash tokens in docker secrets to get around immutable docker secret.

TODO: I need to clean up this repo.


```sh
# put secrets in a temporary location for this example
cp -r test/secrets/ /tmp/secrets

# build the secret hasher
docker-compose -f docker-compose-test.yml build

# create some variables to export
docker-compose -f docker-compose-test.yml run parse >  ./output/secret-tags
# take a look at the variables, for kicks
cat ./output/secret-tags
# export the variables. this syntax is linux-only. what's a cross-platform way to do the same?
export $(grep -v '^#' ./output/secret-tags | xargs)
# recreate the target compose file with the new secret names and deploy the stack
docker-compose -f ./test/input/short.yml config 2>/dev/null | docker stack deploy -c- mystack
# for kicks, take a look at the interpreted compose configuration that was used above
docker-compose -f ./test/input/short.yml config

### test ###
# get the service's container id
container_id=$(for f in $(docker service ps -q mystack_nginx);do docker inspect --format '{{.Status.ContainerStatus.ContainerID}}' $f; break; done)
# show one of the secrets from within the service's container
docker exec -it $container_id cat /run/secrets/aws_inbound_path

# remove orphaned secrets
docker secret rm $(docker secret ls -q) 2> /dev/null || true
```
