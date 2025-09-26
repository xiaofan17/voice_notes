"""The Voice Notes integration."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import intent
import voluptuous as vol

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
    
    # Register services only once (for the first entry)
    if len(hass.data[DOMAIN]) == 1:
        await _register_services(hass)
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def _register_services(hass: HomeAssistant) -> None:
    """Register services for the Voice Notes integration."""
    
    async def add_note_service(call: ServiceCall) -> None:
        """Handle add_note service call."""
        content = call.data.get("content", "")
        
        if not content:
            _LOGGER.warning("No content provided for add_note service")
            return
        
        # Get the first available entry (assuming single entry for now)
        if not hass.data.get(DOMAIN):
            _LOGGER.error("Voice Notes integration not loaded")
            return
            
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        entry_data = hass.data[DOMAIN][entry_id]
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
        
        _LOGGER.info("Added voice note via service: %s", content)
    
    async def complete_note_service(call: ServiceCall) -> None:
        """Handle complete_note service call."""
        note_id = call.data.get("note_id")
        
        if note_id is None:
            _LOGGER.warning("No note_id provided for complete_note service")
            return
        
        # Get the first available entry
        if not hass.data.get(DOMAIN):
            _LOGGER.error("Voice Notes integration not loaded")
            return
            
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        entry_data = hass.data[DOMAIN][entry_id]
        notes_data = entry_data[DATA_NOTES]
        store = entry_data["store"]
        
        # Find and complete the note
        for note in notes_data["notes"]:
            if note["id"] == note_id:
                note["completed"] = True
                break
        else:
            _LOGGER.warning("Note with id %s not found", note_id)
            return
        
        # Save to persistent storage
        await store.async_save(notes_data)
        
        # Update sensor state
        hass.states.async_set(
            f"sensor.voice_notes_count",
            len([n for n in notes_data["notes"] if not n["completed"]]),
            {
                "notes": notes_data["notes"],
                "total_notes": len(notes_data["notes"])
            }
        )
        
        _LOGGER.info("Completed voice note with id: %s", note_id)
    
    async def delete_note_service(call: ServiceCall) -> None:
        """Handle delete_note service call."""
        note_id = call.data.get("note_id")
        
        if note_id is None:
            _LOGGER.warning("No note_id provided for delete_note service")
            return
        
        # Get the first available entry
        if not hass.data.get(DOMAIN):
            _LOGGER.error("Voice Notes integration not loaded")
            return
            
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        entry_data = hass.data[DOMAIN][entry_id]
        notes_data = entry_data[DATA_NOTES]
        store = entry_data["store"]
        
        # Find and delete the note
        original_count = len(notes_data["notes"])
        notes_data["notes"] = [note for note in notes_data["notes"] if note["id"] != note_id]
        
        if len(notes_data["notes"]) == original_count:
            _LOGGER.warning("Note with id %s not found", note_id)
            return
        
        # Save to persistent storage
        await store.async_save(notes_data)
        
        # Update sensor state
        hass.states.async_set(
            f"sensor.voice_notes_count",
            len([n for n in notes_data["notes"] if not n["completed"]]),
            {
                "notes": notes_data["notes"],
                "total_notes": len(notes_data["notes"])
            }
        )
        
        _LOGGER.info("Deleted voice note with id: %s", note_id)
    
    # Register the services
    hass.services.async_register(
        DOMAIN,
        "add_note",
        add_note_service,
        schema=vol.Schema({
            vol.Required("content"): cv.string,
        })
    )
    
    hass.services.async_register(
        DOMAIN,
        "complete_note",
        complete_note_service,
        schema=vol.Schema({
            vol.Required("note_id"): cv.positive_int,
        })
    )
    
    hass.services.async_register(
        DOMAIN,
        "delete_note",
        delete_note_service,
        schema=vol.Schema({
            vol.Required("note_id"): cv.positive_int,
        })
    )
    
    _LOGGER.info("Voice Notes services registered successfully")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove services only when the last entry is removed
        if len(hass.data[DOMAIN]) == 1:
            hass.services.async_remove(DOMAIN, "add_note")
            hass.services.async_remove(DOMAIN, "complete_note")
            hass.services.async_remove(DOMAIN, "delete_note")
            _LOGGER.info("Voice Notes services unregistered")
        
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