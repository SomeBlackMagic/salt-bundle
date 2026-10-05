nginx_installed:
  pkg.installed:
    - name: nginx

nginx_running:
  service.running:
    - name: nginx
    - enable: True
    - require:
      - pkg: nginx_installed
