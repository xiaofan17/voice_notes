"""Voice Notes sensor platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DATA_NOTES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Voice Notes sensor."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = [
        VoiceNotesCountSensor(config_entry.entry_id, entry_data),
        VoiceNotesListSensor(config_entry.entry_id, entry_data),
    ]
    
    async_add_entities(sensors, True)


class VoiceNotesCountSensor(SensorEntity):
    """Sensor for voice notes count."""
    
    def __init__(self, entry_id: str, entry_data: dict[str, Any]) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._entry_data = entry_data
        self._attr_name = "Voice Notes Count"
        self._attr_unique_id = f"{entry_id}_count"
        self._attr_icon = "mdi:note-text"
        self._attr_native_unit_of_measurement = "notes"
    
    @property
    def native_value(self) -> int:
        """Return the number of active notes."""
        notes = self._entry_data[DATA_NOTES]["notes"]
        return len([note for note in notes if not note.get("completed", False)])
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        notes = self._entry_data[DATA_NOTES]["notes"]
        active_notes = [note for note in notes if not note.get("completed", False)]
        completed_notes = [note for note in notes if note.get("completed", False)]
        
        return {
            "total_notes": len(notes),
            "active_notes": len(active_notes),
            "completed_notes": len(completed_notes),
            "last_note": notes[-1] if notes else None,
        }


class VoiceNotesListSensor(SensorEntity):
    """Sensor for voice notes list."""
    
    def __init__(self, entry_id: str, entry_data: dict[str, Any]) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._entry_data = entry_data
        self._attr_name = "Voice Notes List"
        self._attr_unique_id = f"{entry_id}_list"
        self._attr_icon = "mdi:format-list-bulleted"
    
    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        notes = self._entry_data[DATA_NOTES]["notes"]
        active_notes = [note for note in notes if not note.get("completed", False)]
        return f"{len(active_notes)} active notes"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the notes as attributes."""
        notes = self._entry_data[DATA_NOTES]["notes"]
        
        # Format notes for display
        formatted_notes = []
        for note in notes:
            formatted_notes.append({
                "id": note["id"],
                "content": note["content"],
                "created_at": note["created_at"],
                "completed": note.get("completed", False),
            })
        
        return {
            "notes": formatted_notes,
            "notes_count": len(notes),
        }