"""Tests for Dyson humidifier platform."""

from unittest.mock import patch

from libdyson import (
    DEVICE_TYPE_PURE_HUMIDIFY_COOL,
    DysonPureHumidifyCool,
    MessageType,
    WaterHardness,
)
from libdyson.const import AirQualityTarget
import pytest

from custom_components.dyson_local import DOMAIN
from custom_components.dyson_local.humidifier import (
    ATTR_WATER_HARDNESS,
    SERVICE_SET_WATER_HARDNESS,
)
from homeassistant.components.humidifier import (
    ATTR_HUMIDITY,
    ATTR_MODE,
    DOMAIN as HUMIDIFIER_DOMAIN,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_MODE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.components.humidifier.const import MODE_AUTO, MODE_NORMAL
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry

from . import MODULE, NAME, SERIAL, get_base_device, update_device

ENTITY_ID = f"humidifier.{NAME}"


@pytest.fixture
def device() -> DysonPureHumidifyCool:
    """Return mocked device."""
    device = get_base_device(DysonPureHumidifyCool, DEVICE_TYPE_PURE_HUMIDIFY_COOL)
    device.is_on = True
    device.speed = 5
    device.auto_mode = False
    device.oscillation = True
    device.air_quality_target = AirQualityTarget.GOOD
    device.humidification = True
    device.humidification_auto_mode = True
    device.humidity_target = 50
    with patch(f"{MODULE}._async_get_platforms", return_value=["humidifier"]):
        yield device


async def test_state(hass: HomeAssistant, device: DysonPureHumidifyCool):
    """Test entity state and attributes."""
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_MODE] == MODE_AUTO
    assert attributes[ATTR_HUMIDITY] == 50

    er = await entity_registry.async_get_registry(hass)
    assert er.async_get(ENTITY_ID).unique_id == SERIAL

    device.humidification_auto_mode = False
    device.humidity_target = 30
    await update_device(hass, device, MessageType.STATE)
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_MODE] == MODE_NORMAL
    assert attributes[ATTR_HUMIDITY] == 30

    device.humidification = False
    await update_device(hass, device, MessageType.STATE)
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        (SERVICE_TURN_ON, {}, "enable_humidification", []),
        (SERVICE_TURN_OFF, {}, "disable_humidification", []),
        (SERVICE_SET_HUMIDITY, {ATTR_HUMIDITY: 30}, "set_humidity_target", [30]),
        (
            SERVICE_SET_MODE,
            {ATTR_MODE: MODE_AUTO},
            "enable_humidification_auto_mode",
            [],
        ),
        (
            SERVICE_SET_MODE,
            {ATTR_MODE: MODE_NORMAL},
            "disable_humidification_auto_mode",
            [],
        ),
    ],
)
async def test_command(
    hass: HomeAssistant,
    device: DysonPureHumidifyCool,
    service: str,
    service_data: dict,
    command: str,
    command_args: list,
):
    """Test platform services."""
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN, service, service_data, blocking=True
    )
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        (
            SERVICE_SET_WATER_HARDNESS,
            {ATTR_WATER_HARDNESS: "soft"},
            "set_water_hardness",
            [WaterHardness.SOFT],
        ),
        (
            SERVICE_SET_WATER_HARDNESS,
            {ATTR_WATER_HARDNESS: "medium"},
            "set_water_hardness",
            [WaterHardness.MEDIUM],
        ),
        (
            SERVICE_SET_WATER_HARDNESS,
            {ATTR_WATER_HARDNESS: "hard"},
            "set_water_hardness",
            [WaterHardness.HARD],
        ),
    ],
)
async def test_service(
    hass: HomeAssistant,
    device: DysonPureHumidifyCool,
    service: str,
    service_data: dict,
    command: str,
    command_args: list,
):
    """Test custom services."""
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)