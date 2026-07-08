# Merging Family Calendars for the SwitchBot E-Ink Dashboard

**Support my work:** https://buymeacoffee.com/marktiddy

By default, the E-Ink dashboard's calendar views only let you toggle between individual people rather than showing everyone at once. This guide creates a single merged calendar (one `.ics` file, prefixed with each person's name) that updates automatically and can be added as a shared calendar on the display.

> This assumes you already have the `merge_calendars_ha.py` script in your Home Assistant config repo. You just need to configure and wire it up below. [You can find that script here](https://github.com/marktiddy/home-assistant-tutorials/blob/main/merge_calendars_ha.py)

## 1. Configure the Script

1. Open `merge_calendars_ha.py` in Home Assistant's **File Editor**.
2. Edit the top section to add your own calendars and the names you want used as prefixes.
3. By default the script only covers the **last and next 365 days**, since the E-Ink display can't show more than that anyway — adjust if needed.
4. The script outputs a file called `family-calendar.ics`, which will be publicly accessible for SwitchBot to fetch.
   **Important:** Because SwitchBot needs to reach this file from outside your network, your Home Assistant instance must be remotely accessible — e.g. via **Home Assistant Cloud** or a tunnel like **Cloudflare Tunnel**.

## 2. Add a Shell Command

1. Open `configuration.yaml`.
2. Add a `shell_command` entry:

```yaml
shell_command:
  merge_calendars: "python3 /config/merge_calendars_ha.py"
```

3. Save the file.
4. Go to **Settings > Developer Tools**, check the YAML configuration, then do a proper restart of Home Assistant.

## 3. Create an Automation to Run It Regularly

1. Go to **Settings > Automations & Scenes** and create a new automation.
2. Set the trigger to a **Time Pattern** trigger, using `/15` (so it runs every 15 minutes).
3. Set the action to **Perform Action**, and choose `shell_command.merge_calendars`.
4. Save the automation.
5. Open the three-line menu on the automation and **Run Actions** to test it — this should generate the `family-calendar.ics` file.
   The file will be available at:

```
https://your-home-assistant-url/local/family-calendar.ics
```

## 4. Add the Merged Calendar to the E-Ink Display

1. Open the SwitchBot app and go to your **E-Ink device**.
2. Go to **Schedule** and tap **Sync**.
3. Add the merged calendar URL from step 3 above.
4. Go to **Screen Views**, set the new shared calendar to display, and save.
   You should now see a combined family overview on the display, with each event prefixed by the relevant person's name.

**Support my work:** https://buymeacoffee.com/marktiddy
