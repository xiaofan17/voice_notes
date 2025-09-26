"""The Voice Notes integration."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import intent

from .const import DOMAIN, INTENT_ADD_NOTE, DATA_NOTES, STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Voice Notes component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Voice Notes from a config entry."""
    
    # Initialize storage
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load()
    if data is None:
        data = {"notes": []}
    
    # Store data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_NOTES: data,
        "store": store
    }
    
    # Register intent handler
    intent.async_register(hass, AddNoteIntentHandler(entry.entry_id))
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


class AddNoteIntentHandler(intent.IntentHandler):
    """Handle AddVoiceNote intents."""
    
    intent_type = INTENT_ADD_NOTE
    description = "Add a voice note"
    
    # Slot schema for validation
    slot_schema = {
        "content": cv.string
    }
    
    def __init__(self, entry_id: str) -> None:
        """Initialize the intent handler."""
        self.entry_id = entry_id
    
    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        hass = intent_obj.hass
        
        # Get note content from slots
        content = intent_obj.slots.get("content", {}).get("value", "")
        
        if not content:
            response = intent_obj.create_response()
            response.async_set_speech("抱歉，我没有听到笔记内容。")
            return response
        
        # Get storage data
        entry_data = hass.data[DOMAIN][self.entry_id]
        notes_data = entry_data[DATA_NOTES]
        store = entry_data["store"]
        
        # Create new note
        note = {
            "id": len(notes_data["notes"]) + 1,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "completed": False
        }
        
        # Add note to storage
        notes_data["notes"].append(note)
        
        # Save to persistent storage
        await store.async_save(notes_data)
        
        # Update sensor state
        hass.states.async_set(
            f"sensor.voice_notes_count",
            len([n for n in notes_data["notes"] if not n["completed"]]),
            {
                "notes": notes_data["notes"],
                "last_note": note,
                "total_notes": len(notes_data["notes"])
            }
        )
        
        _LOGGER.info("Added voice note: %s", content)
        
        # Create response
        response = intent_obj.create_response()
        response.async_set_speech(f"好的，我已经记下了：{content}")
        
        return response