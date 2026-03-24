# Full Comparison: gitfs vs spm vs salt-bundle (COMPLETE)

## 1. Architecture and Model

| Критерий           | gitfs              | spm             | salt-bundle                         |
|--------------------|--------------------|-----------------|-------------------------------------|
| Основная модель    | Fileserver backend | Package manager | Package manager + dependency system |
| Тип доставки       | runtime pull       | install-time    | install-time (vendor)               |
| Источник           | Git                | .spm пакеты     | .tgz пакеты                         |
| Центр управления   | Salt master        | master/minion   | проект (локально)                   |
| Pull / Push        | Pull               | Push (install)  | Push (artifact)                     |
| Immutable deploy   | ❌                  | ⚠️              | ✅                                   |
| Snapshot состояния | ❌                  | ❌               | ✅                                   |

## 2. Versioning

| Критерий            | gitfs            | spm             | salt-bundle |
|---------------------|------------------|-----------------|-------------|
| Версия              | branch/tag       | version/release | semver      |
| Pin version         | через branch/tag | да              | да          |
| Semver поддержка    | ❌                | ⚠️              | ✅           |
| Version constraints | ❌                | ❌               | ✅           |
| Latest compatible   | ❌                | ❌               | ✅           |
| Lock file           | ❌                | ❌               | ✅           |
| Reproducibility     | ❌                | ⚠️              | ✅           |

## 3. Dependency management

| Критерий                  | gitfs | spm | salt-bundle |
|---------------------------|-------|-----|-------------|
| Dependency declaration    | ❌     | ⚠️  | ✅           |
| Автоматическое разрешение | ❌     | ❌   | ✅           |
| Version constraints       | ❌     | ❌   | ✅           |
| Dependency graph          | ❌     | ❌   | ⚠️          |
| Transitive dependencies   | ❌     | ❌   | ❌           |
| Conflict resolution       | ❌     | ❌   | ❌           |

## 4. Работа с кодом и файлами

| Критерий           | gitfs | spm | salt-bundle |
|--------------------|-------|-----|-------------|
| States (.sls)      | ✅     | ✅   | ✅           |
| Modules (_modules) | ✅     | ✅   | ✅           |
| Pillars            | ❌     | ❌   | ⚠️          |
| Templates/files    | ✅     | ✅   | ✅           |
| Runtime доступ     | ✅     | ❌   | ❌           |
| Offline работа     | ❌     | ✅   | ✅           |

## 5. Доставка модулей

| Критерий          | gitfs       | spm         | salt-bundle |
|-------------------|-------------|-------------|-------------|
| Нужен sync        | ✅           | ⚠️          | ❌           |
| Где лежат модули  | git cache   | extmods     | vendor/     |
| Автозагрузка      | ❌           | ❌           | ✅           |
| Loader интеграция | стандартная | стандартная | plugin      |

## 6. Repository модель

| Критерий       | gitfs     | spm          | salt-bundle    |
|----------------|-----------|--------------|----------------|
| Тип repo       | Git       | spm repo     | HTTP/file repo |
| Индекс         | ❌         | SPM-METADATA | index.yaml     |
| Несколько repo | ✅         | ✅            | ✅              |
| Приоритет repo | ❌         | ❌            | ✅              |
| CDN поддержка  | ❌         | ⚠️           | ✅              |
| Кеширование    | git cache | spm cache    | package cache  |

## 7. CI/CD интеграция

| Критерий                  | gitfs | spm  | salt-bundle |
|---------------------------|-------|------|-------------|
| CI-friendly               | ❌     | ⚠️   | ✅           |
| Build step                | ❌     | ✅    | ✅           |
| Artifact                  | ❌     | .spm | .tgz        |
| Release pipeline          | ❌     | ❌    | ✅           |
| GitHub/GitLab integration | ❌     | ❌    | ✅           |
| Reproducible builds       | ❌     | ❌    | ✅           |

## 8. Runtime поведение

| Критерий                    | gitfs | spm | salt-bundle |
|-----------------------------|-------|-----|-------------|
| Runtime зависимость от сети | ✅     | ❌   | ❌           |
| Runtime обновления          | ✅     | ❌   | ❌           |
| Drift возможен              | ✅     | ⚠️  | ❌           |
| Deterministic execution     | ❌     | ⚠️  | ✅           |

## 9. Производительность

| Критерий         | gitfs   | spm     | salt-bundle |
|------------------|---------|---------|-------------|
| Clone overhead   | высокий | нет     | нет         |
| Fetch overhead   | есть    | нет     | нет         |
| Install overhead | нет     | средний | средний     |
| Runtime latency  | выше    | низкая  | низкая      |
| Масштабируемость | средняя | высокая | высокая     |

## 10. Хранение данных

| Критерий        | gitfs       | spm     | salt-bundle    |
|-----------------|-------------|---------|----------------|
| Где хранится    | gitfs cache | extmods | vendor         |
| История         | полный git  | нет     | нет            |
| Размер          | большой     | средний | контролируемый |
| Garbage control | ❌           | ⚠️      | ✅              |

## 11. Интеграция с Salt

| Критерий              | gitfs | spm | salt-bundle  |
|-----------------------|-------|-----|--------------|
| Fileserver backend    | ✅     | ❌   | ✅ (bundlefs) |
| file_roots            | ❌     | ❌   | ✅            |
| Loader plugin         | ❌     | ❌   | ✅            |
| Прозрачная интеграция | ❌     | ❌   | ✅            |

## 12. Безопасность

| Критерий              | gitfs | spm | salt-bundle |
|-----------------------|-------|-----|-------------|
| SHA256 проверка       | ❌     | ❌   | ✅           |
| Immutable artifact    | ❌     | ❌   | ✅           |
| Supply chain контроль | ❌     | ❌   | ✅           |
| Repo whitelist        | ❌     | ❌   | ✅           |

## 13. UX / DX

| Критерий        | gitfs   | spm       | salt-bundle |
|-----------------|---------|-----------|-------------|
| Простота старта | ✅       | ❌         | ⚠️          |
| Предсказуемость | ❌       | ⚠️        | ✅           |
| Debug           | сложный | сложный   | проще       |
| Dev workflow    | быстрый | медленный | средний     |
| Learning curve  | низкий  | высокий   | средний     |

## 14. Ограничения

| Критерий              | gitfs   | spm    | salt-bundle |
|-----------------------|---------|--------|-------------|
| Нет dependency system | ✅       | ✅      | ❌           |
| Нет lock              | ✅       | ✅      | ❌           |
| Нет transitive deps   | —       | —      | ✅           |
| Runtime coupling      | высокий | низкий | низкий      |

## Summary

- gitfs → runtime config management
- spm → package distribution
- salt-bundle → dependency + artifact system
