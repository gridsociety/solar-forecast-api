#!/bin/sh
# Pull the freshly pushed :latest image on iotcloud, recreate solar_forecast_api
# and wait for the Dockerfile healthcheck to report the new container healthy.
set -u

key_file=$(mktemp)
hosts_file=$(mktemp)
trap 'rm -f "$key_file" "$hosts_file"' EXIT
printf '%s\n' "$SSH_PRIVATE_KEY" > "$key_file"
printf '%s\n' "$SSH_KNOWN_HOSTS" > "$hosts_file"
chmod 600 "$key_file" "$hosts_file"

# Deploying means moving to :latest: if the compose on the server pins the
# service to another tag, pull and up would silently restart the old image,
# so refuse instead.
printf '%s' "$DOCKER_PASSWORD" | ssh -i "$key_file" -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$hosts_file" \
    "$SSH_USER@$SSH_HOST" "
    set -e
    cd $DEPLOY_PATH
    image=\$(docker compose config --images solar_forecast_api)
    case \"\$image\" in
        */solar-forecast-api:latest) ;;
        *)
            echo \"solar_forecast_api uses \$image in the compose, not solar-forecast-api:latest: refusing to deploy\"
            exit 1
            ;;
    esac
    docker login -u $DOCKER_USERNAME --password-stdin $DOCKER_REGISTRY
    docker compose pull solar_forecast_api
    docker compose up -d solar_forecast_api
    for attempt in \$(seq 1 30); do
        status=\$(docker inspect --format '{{.State.Health.Status}}' solar_forecast_api)
        if [ \"\$status\" = healthy ]; then
            echo 'solar_forecast_api is healthy'
            exit 0
        fi
        sleep 5
    done
    echo \"solar_forecast_api did not become healthy (last status: \$status)\"
    exit 1
"
