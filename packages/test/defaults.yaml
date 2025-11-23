default:
  enable: false
  repo:
    enable: false
    debian:
      name: 'deb [arch=amd64] https://pkgs.zabbly.com/incus/stable bookworm main'
      human_name: 'Zabbly Incus repository'
      uri: 'https://pkgs.zabbly.com/incus/stable'
      dist: 'bookworm'
      comps:
        - main
      architecture: amd64
      channel: stable
      key_url: 'https://pkgs.zabbly.com/key.asc'
    redhat:
      name: 'incus-stable'
      baseurl: 'https://pkgs.zabbly.com/incus/stable/rpm/$releasever/$basearch'
      gpgkey: 'https://pkgs.zabbly.com/key.asc'
      enabled: 1
      gpgcheck: 1

  pkg:
    # Main Incus package. Adjust to your distribution (e.g., incus)
    name: incus
    # Extra OS-level dependencies, if any. Override in pillar.
    deps:
      - qemu-kvm
      - lxcfs

  connection:
    type: 'unix'
    socket: /var/lib/incus/unix.socket

  global:
    lxcfs:
      enable: false
      modules:
        loadavg: true
        cfs: true
        memory: true
        cpuset: true
        sysinfo: true
        pidfd: true

  service:
    # Name of the systemd service providing Incus daemon.
    name: incus
    enable: true

  images: {}
    # Example structure (override in pillar):
    # ubuntu2204:
    #   alias: ubuntu/22.04
    #   source:
    #     server: https://images.linuxcontainers.org
    #     alias: ubuntu/22.04
    #     protocol: simplestreams
    #   auto_update: true
    #   public: false
    #   description: Ubuntu 22.04 LTS

  instances: {}
    # Example structure (override in pillar):
    # web-container:
    #   instance_type: container
    #   source:
    #     type: image
    #     alias: ubuntu/22.04
    #   config:
    #     limits.cpu: "2"
    #     limits.memory: 2GiB
    #   profiles:
    #     - default
    #   ephemeral: false

  instance_snapshots: {}
    # Example structure (override in pillar):
    # web-before-update:
    #   instance: web-container
    #   name: before-system-update
    #   stateful: false
    #   description: Snapshot before OS update

  storage: {}
    # Example structure (override in pillar):
    # default:
    #   name: default
    #   config:
    #     driver: zfs
    #     source: tank/incus

  networks: []
    # Example structure (override in pillar):
    # - name: incusbr0
    #   config:
    #     ipv4.address: 10.0.0.1/24
    #     ipv4.nat: "true"
    #     ipv6.address: none

  profiles: []
    # Example structure (override in pillar):
    # - name: default
    #   config:
    #     limits.cpu: "2"
    #     limits.memory: 2GiB
    #   devices:
    #     root:
    #       type: disk
    #       path: /
    #       pool: default

  server_settings: {}
    # Example structure (override in pillar):
    # config:
    #   core.https_address: "[::]:8443"
    #   core.trust_password: "changeme"
    #   images.auto_update_cached: "true"
    #   images.auto_update_interval: "12"
    #   images.compression_algorithm: "zstd"

  server_settings_individual: {}
    # Example structure (override in pillar):
    # https_api:
    #   ensure: present
    #   key: core.https_address
    #   value: "[::]:8443"

  cluster: {}
