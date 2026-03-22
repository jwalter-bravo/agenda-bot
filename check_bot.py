from telegram import Bot
import asyncio

async def check():
    bot = Bot(token='8259940032:AAGZ0MacY_A6sPVPnOPc3rr_G0rq-s8VIqw')
    
    # Verificar que el bot existe
    me = await bot.get_me()
    print(f'✅ Bot conectado: @{me.username}')
    print(f'   ID: {me.id}')
    
    # Verificar webhook
    webhook = await bot.get_webhook_info()
    print(f'📡 Webhook URL: {webhook.url}')
    print(f'   Estado: {"Activado" if webhook.url else "Desactivado"}')
    
    # Buscar mensajes pendientes
    updates = await bot.get_updates()
    print(f'\n📨 Mensajes pendientes: {len(updates)}')
    
    for update in updates:
        if update.message:
            print(f'   - De: {update.message.from_user.id}')
            print(f'     Texto: {update.message.text}')
            print(f'     Comando: {update.message.entities}')

asyncio.run(check())
