import asyncio
import logging
import logging.config
from cbpi.api import *
from cbpi.controller.kettle_controller import KettleController
import time

logger = logging.getLogger("cbpi4-humidfier")

class HumidifierAutoStart(CBPiExtension):

    def __init__(self,cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.run())
        self.controller : KettleController = cbpi.kettle


    async def run(self):
        logger.info("Starting Humidifier Autorun")
        #get all kettles
        self.kettle = self.controller.get_state()
        for id in self.kettle['data']:
            if (id['type']) == "Humidifier Logic":
                try:
                    self.autostart=(id['props']['AutoStart'])
                    logger.info(self.autostart)
                    if self.autostart == "Yes":
                        humdifier_id=(id['id'])
                        self.humdifier=self.cbpi.kettle.find_by_id(humdifier_id)
                        logger.info(self.humdifier)
                        try:
                            if (self.humdifier.instance is None or self.humdifier.instance.state == False):
                                await self.cbpi.kettle.toggle(self.humdifier.id)
                                logger.info("Successfully switched on logic for humidifier{}".format(self.humdifier.id))
                        except Exception as e:
                            logger.error("Failed to switch on for humidifier {} {}".format(self.humdifier.id, e))
                except:
                    pass


@parameters([
             Property.Select(label="AutoStart", options=["Yes","No"],description="Autostart Curing Chamber on cbpi start"),
             Property.Number(label="Target Humidity", configurable=True, description="Curing Chamber Target Humidity"),
             Property.Sensor(label="Humidity Sensor",description="Humidity Sensor"),
             Property.Actor(label="Humidifier",description="Humidifier"),
             Property.Number(label="Maximum On", configurable=True, description="Maximum on time in seconds"),
             Property.Number(label="Minimum Off", configurable=True, description="Minimum off time in seconds")
             ])

class HumidifierLogic(CBPiKettleLogic):
    
    async def run(self):
        try:

            self.kettle = self.get_kettle(self.id)
            self.humidity_sensor = self.props.get("Humidity Sensor", None)
            self.maximum_on = int(self.props.get("Maximum On", 600))
            self.minimum_off = int(self.props.get("Minimum Off", 60))
            self.humidifier = self.props.get("Humidifier", None)

            if self.humidity_sensor is None:
                logger.error("humidity_sensor not set")
                return

            if self.humidifier is None:
                logger.error("humidifier not set")
                return

            current_stage = 0   # 0 = IDLE, 1 = ON, 2 = OFF
            last_stage_change = time.time()
            while self.running == True:
                current_humidity = self.get_sensor_value(self.humidity_sensor).get("value")
                target_humidity = self.props.get("Target Humidity")
                logger.debug(f"current_humidity={current_humidity} target_humidity={target_humidity} stage={current_stage} last-change={last_stage_change}")
                if current_humidity == None:
                    logger.debug("current_humidity not set")
                elif target_humidity == None:
                    logger.debug("target_humidity not set")
                else:
                    target_humidity = int(target_humidity)
                    if current_stage == 0:
                        if current_humidity < target_humidity:
                            current_stage = 1
                            last_stage_change = time.time()
                            await self.actor_on(self.humidifier)
                            logger.debug("Humidifier to stage 1")
                    elif current_stage == 1:
                        if current_humidity > target_humidity or time.time() - last_stage_change > self.maximum_on:
                            current_stage = 2
                            last_stage_change = time.time()
                            await self.actor_off(self.humidifier)
                            logger.debug("Humidifier to stage 2")
                    elif current_stage == 2 and time.time() - last_stage_change > self.minimum_off:
                        current_stage == 0
                        last_stage_change = time.time()
                        logger.debug("Humidifier to stage 3")

                await asyncio.sleep(5)

        except asyncio.CancelledError as e:
            logger.info("asyncio.CancelledError")
            pass
        except Exception as e:
            logger.error("CustomLogic Error {}".format(e))
        finally:
            logger.info("Exit Humidifier")
            await self.actor_off(self.humidifier)
            self.running = False
            await self.actor_off(self.humidifier)

def setup(cbpi):

    cbpi.plugin.register("Humidifier Logic", HumidifierLogic)
    cbpi.plugin.register("Humidifier Autostart", HumidifierAutoStart)  
