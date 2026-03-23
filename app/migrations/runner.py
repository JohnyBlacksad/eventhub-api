from motor.motor_asyncio import AsyncIOMotorDatabase
from app.migrations.base import Migration

from datetime import datetime, timezone
from pathlib import Path
import importlib
import pkgutil



async def get_applied_versions(db: AsyncIOMotorDatabase) -> set:
    '''Получить список примененных миграций'''

    cursor = db.schema_migrations.find({}, {'version': 1})
    docs = await cursor.to_list(length=None)

    return {doc['version'] for doc in docs}


def get_all_migration(db: AsyncIOMotorDatabase) -> list[Migration]:
    '''Найти все файлы миграций и загрузить их'''

    migrations = []

    version_path = Path(__file__).parent / 'versions'

    for module_info in pkgutil.iter_modules([str(version_path)]):
        if module_info.name.startswith('_'):
            continue

        module = importlib.import_module(f'app.migrations.versions.{module_info.name}')

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Migration) and attr is not Migration:
                migrations.append(attr(db))

    return migrations

async def run_migrations(db: AsyncIOMotorDatabase) -> None:
    '''Применить все непремененные миграции'''

    applied = await get_applied_versions(db)

    all_migrations = get_all_migration(db)

    all_migrations.sort(key=lambda m: m.version)

    pending = [m for m in all_migrations if m.version not in applied]

    for migration in pending:
        print(f'Applying migration {migration.version}: {migration.name}')

        await migration.up()

        await db.schema_migrations.insert_one({
            'version': migration.version,
            'name': migration.name,
            'applied_at': datetime.now(timezone.utc)
        })

        print(f"Migration {migration.version} applied")