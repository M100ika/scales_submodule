import asyncio
from sllurp.llrp import LLRPClientFactory
from loguru import logger

READER_IP = '192.168.1.250'  # Укажи свой IP

def on_tag_report(report):
    for tag in report.msgdict['RO_ACCESS_REPORT']['TagReportData']:
        epc = tag['EPC-96'] if 'EPC-96' in tag else tag.get('EPCData', 'UNKNOWN')
        logger.success(f'Tag seen: {epc}')

async def main():
    logger.info("Connecting to reader...")

    factory = LLRPClientFactory(
        tag_report_callback=on_tag_report,
        logger=logger
    )
    client = await factory.connect(READER_IP)

    logger.info("Starting reading session...")
    await client.start()

    # Подождать 10 секунд, чтобы увидеть теги
    await asyncio.sleep(10)

    logger.info("Stopping session...")
    await client.stop()
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
