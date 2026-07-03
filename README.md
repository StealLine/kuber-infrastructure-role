# kuber-infrastructure-role

This role generates an [`infravokimi`](https://github.com/StealLine/Gitops-microservices) infrastructure repository from the files in
`templates/infravokimi`.

Static files are copied to the output directory as-is. Files ending with `.j2`
are rendered with Ansible variables and written without the `.j2` suffix.

## Requirements

- `ansible.posix` collection, because the role uses `ansible.posix.synchronize`.
- `rsync` available on the machine where the role runs.

## Role Variables

| Variable | Required | Default | Example | Description |
| --- | --- | --- | --- | --- |
| `infravokimi_output_dir` | yes | `/tmp/infravokimi` | `/tmp/infravokimi` | Destination directory where the generated infrastructure repository will be written. |
| `gitlab_container_registry` | yes | `container_registry` | `registry.gitlab.com/kubervokimi/vokiappcode` | Container registry prefix used in Kubernetes image references. |
| `website_domain` | yes | `example.com` | `example.com` | Base public domain used for Argo CD, Grafana, Kiali, Prometheus, production, staging, and preview environments. |
| `infrastructure_git_repository` | yes | `repo` | `https://gitlab.com/kubervokimi/infravokimi.git` | Git repository URL used by Argo CD Applications and repository credentials. |
| `gitlab_token_for_argocd` | yes | `token` | `glpat-...` | GitLab token used by Argo CD to access the infrastructure repository. Configure permissions according to the Argo CD repository credentials documentation. |
| `gitlab_username` | yes | `username` | `StealLine` | GitLab username stored together with GitLab credentials. |
| `gitlab_token_for_imagepullkuber` | yes | `token` | `glpat-...` | GitLab token used by Kubernetes `imagePullSecrets` to pull images from the registry. It must have permission to read the registry. |
| `gitlab_b64_auth` | yes | `gitlab_username:gitlab_token_for_imagepullkuber` | base64 of `username:token` | Base64 registry auth value used in the `dockerconfigjson` secret. |
| `production_s3_service_url` | yes | `s3_url` | `https://storage.yandexcloud.net` | Production S3-compatible endpoint URL. This setup was tested with Yandex S3; other S3-compatible providers may need extra changes. |
| `s3_prod_access_key` | yes | `your-s3-access-key` | `your-access-key` | Production S3 access key. |
| `s3_prod_secret_key` | yes | `your-s3-secret-key` | `your-secret-key` | Production S3 secret key. |
| `resend_token` | yes | `your-resend-token` | `re_...` | Resend SMTP/API password rendered into `auth-extra.env`. |
| `grafana_admin_password` | no | `pass` | `your-grafana-password` | Grafana admin password used in the kube-prometheus-stack values. |

The defaults are placeholders. Override all required
variables with environment-specific values.

## Example Playbook

```yaml
- hosts: localhost
  gather_facts: false
  roles:
    - role: kuber-infrastructure-role
      vars:
        infravokimi_output_dir: /tmp/infravokimi
        gitlab_container_registry: registry.gitlab.com/kubervokimi/vokiappcode
        website_domain: example.com
        infrastructure_git_repository: https://gitlab.com/kubervokimi/infravokimi.git
        gitlab_username: your-gitlab-username
        gitlab_token_for_argocd: your-argocd-repo-token
        gitlab_token_for_imagepullkuber: your-registry-read-token
        gitlab_b64_auth: your-base64-username-token
        production_s3_service_url: https://storage.yandexcloud.net
        s3_prod_access_key: your-s3-access-key
        s3_prod_secret_key: your-s3-secret-key
        resend_token: your-resend-token
        grafana_admin_password: your-grafana-password
```

## Dependencies

No role dependencies are defined.

## License

MIT-0

## Author Information

StealLine
