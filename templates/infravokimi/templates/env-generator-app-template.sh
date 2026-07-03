#!/usr/bin/bash


set -eu


S="overlays/mr-${MR_NUMBER}/secrets"

mkdir -p "$S"

REGISTRY_AUTH="$(printf '%s:%s' "${REGISTRY_USER}" "${REGISTRY_PASSWORD}" | base64 | tr -d '\n')"

cat > "$S/gitlab-registry.dockerconfigjson" << END
{
  "auths": {
    "${REGISTRY}": {
      "username": "${REGISTRY_USER}",
      "password": "${REGISTRY_PASSWORD}",
      "auth": "${REGISTRY_AUTH}"
    }
  }
}
END

cat > "$S/postgres.env" << END
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB}
END


cat > "$S/minio.env" << END
MINIO_BROWSER_REDIRECT_URL=${MINIO_BROWSER_REDIRECT_URL}
END

printf '%s' "${JWT_PUBLIC_KEY_B64}" | base64 -d > "$S/jwt-public.pem"
printf '%s' "${AUTH_PRIVATE_KEY_B64}" | base64 -d > "$S/jwt-private.pem"

cat > "$S/common.env" << ENV
MessageBroker__Username=${RABBITMQ_USERNAME}
MessageBroker__Password=${RABBITMQ_PASSWORD}
S3__AccessKey=${MINIO_USER}
S3__SecretKey=${MINIO_PASSWORD}
ENV

cat > "$S/auth-extra.env" << END
EmailServiceConfig__Host=${SMTP_HOST}
EmailServiceConfig__Port=${SMTP_PORT}
EmailServiceConfig__Username=${SMTP_USERNAME}
EmailServiceConfig__Password=${SMTP_PASSWORD}
END


db() {
  local key="$1"
  local database="$2"
  local output="$3"

  cat > "$S/${output}" << END
${key}=Host=postgres;Port=5432;User Id=${POSTGRES_USER};Password=${POSTGRES_PASSWORD};Database=${database};SslMode=Disable
END
}

db ConnectionStrings__AuthServiceDb          vokimi_auth_service_db                auth-service.env
db ConnectionStrings__AlbumsServiceDb        vokimi_albums_service_db              albums-service.env
db ConnectionStrings__TagsServiceDb          vokimi_tags_service_db                tags-service.env
db ConnectionStrings__UserProfilesServiceDb  vokimi_user_profiles_service_db       user-profiles-service.env
db ConnectionStrings__VokiCommentsServiceDb  vokimi_voki_comments_service_db       voki-comments-service.env
db ConnectionStrings__VokiRatingsServiceDb   vokimi_voki_ratings_service_db        voki-ratings-service.env
db ConnectionStrings__VokisCatalogServiceDb  vokimi_vokis_catalog_service_db       vokis-catalog-service.env
db ConnectionStrings__CoreVokiCreationServiceDb    vokimi_voki_creation_core_service_db    core-voki-creation-service.env
db ConnectionStrings__GeneralVokiCreationServiceDb vokimi_voki_creation_general_service_db general-voki-creation-service.env
db ConnectionStrings__GeneralVokiTakingServiceDb   vokimi_voki_taking_general_service_db   general-voki-taking-service.env

echo "Application secrets generated for ${MR_NUMBER}: $S"