from bluepy.btle import DefaultDelegate
from logger.logger import get_logger

logger = get_logger(__name__)


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            logger.info(f"Discovered device {dev.addr}")
        elif isNewData:
            logger.info(f"Received new data from {dev.addr}")
