"""Config flow for Siemens PLC"""
from __future__ import annotations

import ipaddress
import logging
import re
import traceback

import snap7
import getmac
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS
import voluptuous as vol

from .const import *
from .common import get_lib_location

_LOGGER = logging.getLogger(__name__)

class SiemensS7ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Siemens PLC config flow."""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial Button+ setup, showing the 2 options."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["logo", "s7"],
        )

    async def async_step_logo(self, user_input=None):
        """Siemens PLC configuration step for Logo! PLC's"""
        errors = {}
        name = None
        ip = None
        local_tsap = None
        remote_tsap = None
        logo_connection_result = None
        
        _LOGGER.debug(f"{DOMAIN} Siemens Logo! PLC step {user_input}")

        if user_input is not None:
            name              = user_input["name"]
            ip                = user_input.get(CONF_IP_ADDRESS, None)
            local_tsap        = user_input["local_tsap"]
            remote_tsap       = user_input["remote_tsap"]

            valid_ip          = self.validate_ip(ip)
            valid_local_tsap  = self.validate_tsap_id(local_tsap) 
            valid_remote_tsap = self.validate_tsap_id(remote_tsap)

            if valid_ip and valid_local_tsap and valid_remote_tsap:
                try:
                    _LOGGER.debug(f"{DOMAIN} Connecting PLC at ip: {ip}")
                    library_location = get_lib_location()
                    snap7.logo.load_library(library_location)
                    client = snap7.logo.Logo()
                    logo_connection_result = client.connect(ip, int(local_tsap, 16), int(remote_tsap, 16))
                    if logo_connection_result is None:
                        client.disconnect()
                        return self.async_create_entry(
                            title=f"{name}",
                            description=f"Siemens Logo! on {ip} with id s7_{ getmac.get_mac_address(ip=ip).replace(':', '') }",
                            data={
                                "type": "logo",
                                "id": f"logo_{ getmac.get_mac_address(ip=ip).replace(':', '') }",
                                "connection": {
                                    "ip": ip,
                                    "local_tsap": local_tsap,
                                    "remote_tsap": remote_tsap
                                }
                            }
                        )
                    else:
                        raise ConnectionError


                except ConnectionError as ex:
                    _LOGGER.error(
                        f"{DOMAIN} Could not connect the Siemens Logo! with IP {ip}, local_tsap {local_tsap}, remote_tsap {remote_tsap}, connection_result {logo_connection_result}\n Exception: %s - traceback: %s",
                        ex,
                        traceback.format_exc()
                    )
                    errors["base"] = "error_cannot_connect"

                except Exception as ex:
                    _LOGGER.error(
                        f"{DOMAIN} Exception: %s - traceback: %s",
                        ex,
                        traceback.format_exc()
                    )
                    errors["base"] = "error_cannot_connect"

            else:
                if not valid_local_tsap:
                    errors["base"] = 'error_invalid_local_tsap'
                if not valid_remote_tsap:
                    errors["base"] = 'error_invalid_remote_tsap'
                if not valid_ip:
                    errors["base"] = 'error_invalid_ip'

        return self.async_show_form(
            step_id="logo",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): vol.All(str, vol.Length(2, 128)),
                    CONF_IP_ADDRESS: str,
                    vol.Required("local_tsap"): vol.All(str, vol.Length(4, 4), vol.Match(r'^[a-fA-F0-9]+$')),
                    vol.Required("remote_tsap"): vol.All(str, vol.Length(4, 4), vol.Match(r'^[a-fA-F0-9]+$')),
                }
            ),
            errors=errors ,
            description_placeholders={
                "name": name,
                "ip": ip,
                "local_tsap": local_tsap,
                "remote_tsap": remote_tsap
            }
        )

    async def async_step_s7(self, user_input=None):
        """Siemens PLC configuration step for Logo! PLC's"""
        errors = {}
        name = None
        ip = None
        rack = None
        slot = None
        s7_connection_result = None

        _LOGGER.debug(f"{DOMAIN} Siemens S7 PLC step {user_input}")

        if user_input is not None:
            name = user_input["name"]
            ip   = user_input.get(CONF_IP_ADDRESS, None)
            rack = user_input["rack"]
            slot = user_input["slot"]

            valid_ip   = self.validate_ip(ip)
            valid_rack = self.validate_rack_slot(rack)
            valid_slot = self.validate_rack_slot(slot)

            if valid_ip and valid_rack and valid_slot:
                try:
                    _LOGGER.debug(f"{DOMAIN} Connecting PLC at ip: {ip}")
                    library_location = get_lib_location()
                    client = snap7.client.Client(lib_location=library_location)
                    s7_connection_result = client.connect(ip, rack, slot)
                    if s7_connection_result == 0:
                        client.disconnect()
                        return self.async_create_entry(
                            title=f"{name}",
                            description=f"Siemens S7 PLC on {ip} with id s7_{ getmac.get_mac_address(ip=ip).replace(':', '') }",
                            data={
                                "type": "s7",
                                "id": f"s7_{ getmac.get_mac_address(ip=ip).replace(':', '') }",
                                "connection": {
                                    "ip": ip,
                                    "rack": rack,
                                    "slot": slot
                                }
                            }
                        )
                    else:
                        raise ConnectionError


                except ConnectionError as ex:
                    _LOGGER.error(
                        f"{DOMAIN} Could not connect the Siemens S7 PLC with IP {ip}, rack {rack}, slot {slot}, s7_connection_result {s7_connection_result}\n Exception: %s - traceback: %s",
                        ex,
                        traceback.format_exc()
                    )

                    errors["base"] = "Error connecting to {ip}"
                except Exception as ex:
                    _LOGGER.error(
                        f"{DOMAIN} Exception: %s - traceback: %s",
                        ex,
                        traceback.format_exc()
                    )

                    errors["base"] = "error_cannot_connect"

            else:
                if not valid_rack:
                    errors["base"] = 'error_invalid_rack'
                if not valid_slot:
                    errors["base"] = 'error_invalid_slot'
                if not valid_ip:
                    errors["base"] = 'error_invalid_ip'

        return self.async_show_form(
            step_id="s7",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): vol.All(str, vol.Length(2, 128)),
                    CONF_IP_ADDRESS: str,
                    vol.Required("rack"): vol.All(int, vol.Range(0, 63)),
                    vol.Required("slot"): vol.All(int, vol.Range(0, 63)),
                }
            ),
            errors=errors ,
            description_placeholders={
                "name": name,
                "ip": ip,
                "rack": rack,
                "slot": slot
            }
        )

    @staticmethod
    def validate_ip(ip) -> bool:
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_rack_slot(slot) -> bool:
        return type(slot) is int and RACKSLOT_MIN <= slot <= RACKSLOT_MAX

    @staticmethod
    def validate_tsap_id(tsap_id) -> bool:
        return len(tsap_id) == 4 and re.match(r'^[a-fA-F0-9]+$', tsap_id)