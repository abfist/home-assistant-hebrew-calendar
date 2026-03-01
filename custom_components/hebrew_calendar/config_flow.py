"""
Config Flow for Hebrew Calendar Events
=======================================
מאפשר הגדרת ה-integration דרך ממשק המשתמש של HA.
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class HebrewCalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Config Flow להגדרת Hebrew Calendar Events.
    מאפשר התקנה דרך Settings > Integrations > Add Integration.
    """

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """
        שלב ראשון: המשתמש מאשר את ההתקנה.
        ה-integration אינו דורש קונפיגורציה מיוחדת בשלב זה.
        """
        # בדיקה שה-integration לא כבר מותקן
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Hebrew Calendar Events",
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "description": "אינטגרציה לניהול אירועים בלוח שנה עברי"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """החזרת options flow לאפשרויות נוספות."""
        return HebrewCalendarOptionsFlow(config_entry)


class HebrewCalendarOptionsFlow(config_entries.OptionsFlow):
    """Options Flow לאפשרויות מתקדמות."""

    def __init__(self, config_entry):
        """אתחול עם ה-entry הקיים."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """שלב ראשון של options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
