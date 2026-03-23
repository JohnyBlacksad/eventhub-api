from app.migrations.base import Migration
from pymongo import TEXT

class Migration001(Migration):

    version = '001'
    name = 'initial_indexes'

    async def up(self):
        '''Применить миграцию: Создать индексы.'''

        users = self.db['users']
        await users.create_index('email', unique=True)

        events = self.db['events']
        await events.create_index('created_by')
        await events.create_index('startDate')
        await events.create_index('status')

        await events.create_index([('title', TEXT)])
        await events.create_index([('location.city', 1), ('status', 1)])
        await events.create_index([('deleted_at', 1)], expireAfterSeconds=0)

        registrations = self.db['registrations']
        await registrations.create_index([('event_id', 1), ('user_id', 1)], unique=True)
        await registrations.create_index('user_id')

        codes = self.db['org_code']
        await codes.create_index('code', unique=True)
        await codes.create_index('activated_by')


    async def down(self):
        '''Откатить миграцию: Удалить индексы.'''

        users = self.db['users']
        await users.drop_index('email_1')

        events = self.db['events']
        await events.drop_index('created_by_1')
        await events.drop_index('startDate_1')
        await events.drop_index('status_1')

        await events.drop_index('title_text')
        await events.drop_index('location.city_1_status_1')
        await events.drop_index('deleted_at_1')

        registrations = self.db['registrations']
        await registrations.drop_index('event_id_1_user_id_1')
        await registrations.drop_index('user_id_1')

        codes = self.db['org_code']
        await codes.drop_index('code_1')
        await codes.drop_index('activated_by_1')