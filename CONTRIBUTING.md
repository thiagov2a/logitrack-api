# Guía de Contribución — LogiTrack

## Configuración del entorno

```bash
git clone https://github.com/thiagov2a/logitrack-api.git
cd logitrack-api
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Estrategia de ramas

| Rama | Uso |
|---|---|
| `main` | Código estable, solo se actualiza via PR |
| `feat/US-XX-descripcion` | Nueva funcionalidad |
| `fix/US-XX-descripcion` | Corrección de bug |
| `refactor/descripcion` | Refactorización sin cambio funcional |
| `docs/descripcion` | Documentación |

## Convención de commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: descripción corta
fix: descripción corta
refactor: descripción corta
docs: descripción corta
test: descripción corta
chore: descripción corta
```

Ejemplos:
```
feat: agrega endpoint de cambio de estado (US-08)
fix: corrige validacion de tracking ID inexistente
test: agrega tests para US-12
```

## Flujo de trabajo

1. Crear rama desde `main`: `git checkout -b feat/US-XX-descripcion`
2. Desarrollar y commitear con la convención de commits
3. Correr linter y tests antes de pushear:
   ```bash
   flake8 . --max-line-length=120 --exclude=venv
   pytest tests/ -v
   ```
4. Abrir Pull Request hacia `main`
5. El pipeline de CI debe pasar antes de hacer merge

## Equipo

- Mauricio Santiago **Quevedo** — 46.340.138
- Pablo Ariel **Rodriguez** — 39.109.268
- Thiago Joel **Vildosa** — 45.815.384
