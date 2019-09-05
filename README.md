# docker-secret-hash
Use hash tokens in docker compose secret names to get around immutable docker secret limitations. (See https://github.com/moby/moby/issues/29882#issuecomment-475807643 )

This uses file-based secrets. The secret hasher image would need to be tweaked if the secrets came from some other secret store.

TODO: I need to clean up this repo.

## Premise


Your project's `docker-compose.yml` would have its secrets defined with the following convention.

```yaml
...
secrets:
  aws_inbound_path:
    file: /tmp/secrets/aws_inbound_path
    name: aws_inbound_path-${SECRET_SUM_aws_inbound_path:-0}
  cfml_app_secrets:
    file: /tmp/secrets/credentials.properties
    name: cfml_app_secrets-${SECRET_SUM_cfml_app_secrets:-0}
...
```

The compose file will get parsed by the routines in this GitHub project and an INI-like file will be output, which looks like the following. The value on the right side of the `=` is the md5sum of the _contents_ of the secret file.

```sh
# aws_inbound_path /secrets/aws_inbound_path
SECRET_SUM_aws_inbound_path=900150983cd24fb0d6963f7d28e17f72
# cfml_app_secrets /secrets/credentials.properties
SECRET_SUM_cfml_app_secrets=4ed9407630eb1000c0f6b63842defa7d
```

In your project's build process (demonstrated later under the "Example" heading), a command is run that ends up doing this automatically:

```sh
export SECRET_SUM_aws_inbound_path=5ce25192496704043f42c835aaf6e61e
export SECRET_SUM_cfml_app_secrets=d00d41c9779437670b6c2d098bd7f9e3
```

Which makes those variables available for normal `docker-compose` commands.

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
