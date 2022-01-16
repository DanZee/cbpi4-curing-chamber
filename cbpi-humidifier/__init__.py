import asyncio
import logging
from cbpi.api import *
from cbpi.controller.kettle_controller import KettleController

class HumidifierAutoStart(CBPiExtension):

    def __init__(self,cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.run())
        self.controller : KettleController = cbpi.kettle


    async def run(self):
        logging.info("Starting Humidifier Autorun")
        #get all kettles
        self.kettle = self.controller.get_state()
        for id in self.kettle['data']:
            if (id['type']) == "Humidifier":
                try:
                    self.autostart=(id['props']['AutoStart'])
                    logging.info(self.autostart)
                    if self.autostart == "Yes":
                        humdifier_id=(id['id'])
                        self.humdifier=self.cbpi.kettle.find_by_id(humdifier_id)
                        logging.info(self.humdifier)
                        try:
                            if (self.humdifier.instance is None or self.humdifier.instance.state == False):
                                await self.cbpi.kettle.toggle(self.humdifier.id)
                                logging.info("Successfully switched on logic for humidifier{}".format(self.humdifier.id))
                        except Exception as e:
                            logging.error("Failed to switch on for humidifier {} {}".format(self.humdifier.id, e))
                except:
                    pass


@parameters([
             Property.Select(label="AutoStart", options=["Yes","No"],description="Autostart Curing Chamber on cbpi start"),
             Property.Number(label="TargetHumidity", configurable=True, description="Curing Chamber Target Humidity"),
             Property.Sensor(label="Humidity Sensor",description="Humidity Sensor"),
             Property.Actor(label="Humidfier",description="Humidifier"),
             Property.Number(label="Maximum On", configurable=True, description="Maximum on time in seconds"),
             Property.Number(label="Minimum Off", configurable=True, description="Minimum off time in seconds")
             ])

class HumidifierLogic(CBPiKettleLogic):
    
    async def run(self):
        try:

            # self.kettle = self.get_kettle(self.id)
            # self.heater = self.kettle.heater
            # self.cooler = self.kettle.agitator

            # target_temp = self.get_kettle_target_temp(self.id)
            # if target_temp == 0:
            #     await self.set_target_temp(self.id,int(self.props.get("TargetTemp", 0)))
 

            # while self.running == True:
                
            #     sensor_value = self.get_sensor_value(self.kettle.sensor).get("value")
            #     target_temp = self.get_kettle_target_temp(self.id)

            #     if sensor_value + self.heater_offset_min <= target_temp:
            #         if self.heater:
            #             await self.actor_on(self.heater)
                    
            #     if sensor_value + self.heater_offset_max >= target_temp:
            #         if self.heater:
            #             await self.actor_off(self.heater)

            #     if sensor_value >=  self.cooler_offset_min + target_temp:
            #         if self.cooler:
            #             await self.actor_on(self.cooler)
                    
            #     if sensor_value <= self.cooler_offset_max + target_temp:
            #         if self.cooler:
            #             await self.actor_off(self.cooler)

                await asyncio.sleep(1)

        except asyncio.CancelledError as e:
            pass
        except Exception as e:
            logging.error("CustomLogic Error {}".format(e))
        finally:
            self.running = False
            # if self.heater:
            #     await self.actor_off(self.heater)
            # if self.cooler:
            #     await self.actor_off(self.cooler)

def setup(cbpi):

    cbpi.plugin.register("Curing Chamber Logic", HumidifierLogic)
    cbpi.plugin.register("Curing Chamber Autostartt", HumidifierAutoStart)  
