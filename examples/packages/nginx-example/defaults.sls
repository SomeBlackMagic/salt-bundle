{% set defaults = salt['grains.filter_by']({
    'Debian': {
        'package_name': 'nginx',
        'service_name': 'nginx',
        'config_path': '/etc/nginx/nginx.conf',
    },
    'RedHat': {
        'package_name': 'nginx',
        'service_name': 'nginx',
        'config_path': '/etc/nginx/nginx.conf',
    },
}) %}
