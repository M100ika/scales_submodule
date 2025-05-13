import asyncio
import sllurp.llrp as llrp

async def main():
    reader = llrp.LLRPClientFactory()
    await reader.connect('192.168.1.250', 60000)
    await reader.start()

    # Запрос информации о считывателе
    await reader.get_reader_capabilities()
    await reader.get_reader_config()

    # Ожидание получения сообщений
    await asyncio.sleep(5)

    await reader.stop()
    await reader.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
