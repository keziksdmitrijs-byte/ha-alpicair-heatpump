from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from .const import *
def pts(s): return sorted((float(a),float(b)) for a,b in (x.strip().split(":") for x in s.split(",")))
def calc(p,x):
 if x<=p[0][0]: return p[0][1]
 if x>=p[-1][0]: return p[-1][1]
 for (a,b),(c,d) in zip(p,p[1:]):
  if a<=x<=c:return b+(d-b)*(x-a)/(c-a)
async def async_setup_entry(hass,entry,async_add_entities): async_add_entities([Curve(entry)],update_before_add=True)
class Curve(SensorEntity):
 _attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
 _attr_should_poll=True
 def __init__(self,e): self.e=e;self._attr_name="Calculated flow temperature";self._attr_unique_id=e.entry_id+"_flow";self._v=None
 async def async_update(self):
  s=self.hass.states.get(self.e.data[CONF_OUTDOOR_ENTITY])
  if s and s.state not in ("unknown","unavailable"):
   v=calc(pts(self.e.data[CONF_POINTS]),float(s.state));self._v=round(max(float(self.e.data[CONF_MIN_TEMP]),min(float(self.e.data[CONF_MAX_TEMP]),v)))
   target=self.e.data.get(CONF_TARGET_ENTITY)
   if target:
    domain="input_number" if target.startswith("input_number.") else "number"
    await self.hass.services.async_call(domain,"set_value",{"entity_id":target,"value":self._v})
 @property
 def native_value(self):return self._v
 @property
 def extra_state_attributes(self):return {"outdoor_entity":self.e.data[CONF_OUTDOOR_ENTITY],"target_entity":self.e.data.get(CONF_TARGET_ENTITY),"curve_points":self.e.data[CONF_POINTS],"step":self.e.data[CONF_STEP]}
