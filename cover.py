"""Support for Freebox covers."""
import logging
import json
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.cover import CoverEntity, DEVICE_CLASS_SHUTTER
from .const import DOMAIN
from .base_class import FreeboxBaseClass

from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    router = hass.data[DOMAIN][entry.unique_id]
    tracked = set()

    @callback
    def update_router():
        add_entities(hass, router, async_add_entities, tracked)

    router.listeners.append(async_dispatcher_connect(hass, router.signal_device_new, update_router))
    update_router()

@callback
def add_entities(hass, router, async_add_entities, tracked):
    """Add new cover from the router."""
    new_tracked = []
    for nodeId, node in router.nodes.items():
        if (node["category"]!="basic_shutter") or (node["id"] in tracked):
            continue
        new_tracked.append(FreeboxBasicShutter(hass, router, node))
        tracked.add(node["id"] )

    if new_tracked:
        async_add_entities(new_tracked, True)



class FreeboxBasicShutter(FreeboxBaseClass,CoverEntity):

    def __init__(self, hass, router, node) -> None:
        """Initialize a Cover"""
        super().__init__(hass, router, node)
        self._command_up    = self.get_command_id(node['show_endpoints'], "slot", "up")
        self._command_stop  = self.get_command_id(node['show_endpoints'], "slot", "stop")
        self._command_down  = self.get_command_id(node['show_endpoints'], "slot", "down")
        self._command_state = self.get_command_id(node['show_endpoints'], "signal", "state")
        self._state         = self.get_node_value(node['show_endpoints'], "signal", "state")

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_SHUTTER

    @property
    def current_cover_position(self):
        return None

    @property
    def current_cover_tilt_position(self):
        return None

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        if(self._state == STATE_OPEN):
            return False
        if(self._state == STATE_CLOSED):
            return True
        return None

    async def async_open_cover(self, **kwargs):
        """Open cover."""
        await self.set_home_endpoint_value(self._command_up, {"value": None})
        self._state = STATE_OPEN

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self.set_home_endpoint_value(self._command_down, {"value": None})
        self._state = STATE_CLOSED

    async def async_stop_cover(self, **kwargs):
        """Stop cover."""
        await self.set_home_endpoint_value(self._command_stop, {"value": None})
        self._state = None

    async def async_update(self):
        """Get the state & name and update it."""
        node = self._router.nodes[self._id];
        self._name = node["label"].strip()
        self._state = self.convert_state(await self.get_home_endpoint_value(self._command_state))
        

    def convert_state(self, state):
        if( state ): 
            return STATE_CLOSED
        elif( state is not None):
            return STATE_OPEN
        else:
            return None