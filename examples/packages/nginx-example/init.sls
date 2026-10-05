{% from "nginx-example/defaults.sls" import defaults with context %}

nginx_pkg:
  pkg.installed:
    - name: {{ defaults.package_name }}

nginx_service:
  service.running:
    - name: {{ defaults.service_name }}
    - enable: True
    - require:
      - pkg: nginx_pkg

nginx_config:
  file.managed:
    - name: {{ defaults.config_path }}
    - source: salt://nginx-example/nginx/nginx.conf.jinja
    - template: jinja
    - watch_in:
      - service: nginx_service
