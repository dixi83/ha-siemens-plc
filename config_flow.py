"""Config flow for Siemens PLC"""
from __future__ import annotations

import ipaddress
import logging
import traceback
import os

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_IP_ADDRESS
import voluptuous as vol

from .const import DOMAIN

import snap7

_LOGGER = logging.getLogger(__name__)

class SiemensS7ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Siemens PLC config flow."""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial Button+ setup, showing the 2 options."""
        _LOGGER.info(f"{DOMAIN} Current path is {__file__}")
        return self.async_show_menu(
            step_id="user",
            menu_options=["logo", "s7"],
        )

    async def async_step_logo(self, user_input=None):
        errors = {}

        _LOGGER.debug(f"Fetch website step {user_input}")

        ip = None

        if user_input is not None:
            ip = user_input.get(CONF_IP_ADDRESS, None)
            local_tsap = user_input["local_tsap"]
            remote_tsap = user_input["remote_tsap"]
            valid_ip          = self.validate_ip(ip) 
            valid_local_tsap  = self.validate_tsap_id(local_tsap) 
            valid_remote_tsap = self.validate_tsap_id(remote_tsap)

            if valid_ip and valid_local_tsap and valid_remote_tsap:
                try:
                    _LOGGER.debug(f"Connecting PLC at ip: {ip}")
                    client = snap7.logo.Logo(lib_location=f"{os.getcwd()}/lib/libsnap7.so")
                    result = client.connect(ip, int(local_tsap, 16), int(remote_tsap, 16))
                    if result == None:
                        client.disconnect()
                        return self.async_create_entry(
                            title=f"{device_config.core.name}",
                            description=f"Base module on {ip} with id {device_config.info.device_id}",
                            data={"config": json_config}
                        )
                    else:
                        raise ConnectionError


                except ConnectionError as ex:  # pylint: disable=broad-except
                    _LOGGER.error(
                        f"{DOMAIN} Could not connect the Siemens Logo! with IP {ip}, local_tsap {local_tsap}, remote_tsap {remote_tsap}, result {result}\n Exception: %s - traceback: %s",
                        ex,
                        traceback.format_exc()
                    )
                    errors["base"] = "cannot_connect"

                except Exception as ex:  # pylint: disable=broad-except
                    _LOGGER.error(
                        f"{DOMAIN} Exception: %s - traceback: %s",
                        ex,
                        traceback.format_exc()
                    )
                    errors["base"] = "cannot_connect"

            else:
                if not valid_local_tsap:
                    errors["base"] = 'invalid_local_tsap'
                if not valid_remote_tsap:
                    errors["base"] = 'invalid_remote_tsap'
                if not valid_ip:
                    errors["base"] = 'invalid_ip'

        return self.async_show_form(
            step_id="logo",
            data_schema=vol.Schema(
                {
                    CONF_IP_ADDRESS: str,
                    vol.Required("tsap_local"): str,
                    vol.Required("tsap_remote"): str,
                }
            ),
            errors=errors #,
            # description_placeholders={
            #     "ip": ip
            # }
        )

    async def async_step_s7(self, user_input=None):
        errors = {}
        ip = None
        if user_input is not None:
            ip = user_input.get(CONF_IP_ADDRESS, None)
            rack = user_input["rack"]
            slot = user_input["slot"]
            valid = (
                    self.validate_ip(ip)
                and self.validate_rack(rack)
                and self.validate_slot(slot)
            )
            if valid:
                try:
                    _LOGGER.debug(f"Connecting PLC at ip: {ip}")
                    client = snap7.client.Client(lib_location=f"{os.path.dirname(os.path.abspath(__file__))}/lib/libsnap7.so")
                    result = client.connect(ip, rack, slot) 
                    if result == 0:
                        client.disconnect()
                        return self.async_create_entry(
                            title=f"{device_config.core.name}",
                            description=f"Base module on {ip} with id {device_config.info.device_id}",
                            data={"config": json_config}
                        )
                    else:
                        raise ConnectionError


                except ConnectionError as ex:  # pylint: disable=broad-except
                    _LOGGER.error(
                        f"{DOMAIN} Could not connect the Siemens S7 PLC with IP {ip}, rack {rack}, slot {slot}, result {result}\n Exception: %s - traceback: %s",
                        ex,
                        traceback.format_exc()
                    )

                    errors["base"] = "Error connecting to {ip}"
                except Exception as ex:  # pylint: disable=broad-except
                    _LOGGER.error(
                        f"{DOMAIN} Exception: %s - traceback: %s",
                        ex,
                        traceback.format_exc()
                    )

                    errors["base"] = "cannot_connect"

            else:
                errors["base"] = 'invalid_ip'

        return self.async_show_form(
            step_id="s7",
            data_schema=vol.Schema(
                {
                    CONF_IP_ADDRESS: str,
                    vol.Required("rack"): int,
                    vol.Required("slot"): int
                }
            ),
            errors=errors #,
            # description_placeholders={
            #     "ip": ip
            # }
        )

    def validate_ip(self, ip) -> bool:
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ValueError:
            return False
            
    def validate_rack(self, rack) -> bool:
        return type(rack) is int

    def validate_slot(self, slot) -> bool:
        return type(slot) is int

    def validate_tsap_id(self, tsap_id) -> bool:
        return len(tsap_id) == 4
