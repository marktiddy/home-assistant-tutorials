# Setting Up a Custom Screen on the SwitchBot E-Ink Dashboard

**Support my work:** https://buymeacoffee.com/marktiddy

This guide walks through enabling a custom screen on the SwitchBot E-Ink Home Dashboard, driven by the SwitchBot API and triggered from Home Assistant.

## 1. Enable the Custom Screen

1. Open the E-Ink display's settings.
2. Go to **Screen Views**.
3. Add **Custom**.
4. Toggle it to update **via SwitchBot API**.

## 2. Get Your SwitchBot API Key

1. Open the SwitchBot app and go to **Profile**.
2. Go to **Preferences > About**.
3. Tap the **App Version** at least 5 times in quick succession to unlock **Developer Options**.
4. In Developer Options, generate a new **Token** and **Secret**.
5. Note both down and keep them private.

## 3. Find Your Weather Station's Device ID

1. Use an API testing tool such as [reqbin.com](https://reqbin.com) or an app like **Postman**.
2. Make a **GET** request to:

```
   https://api.switch-bot.com/v1.1/devices
```

3. Add an **Authorization** header containing your Token.
4. Send the request — this returns a list of your devices.
5. Find your **Weather Station** entry and note its `deviceId`.

## 4. Add a REST Command in Home Assistant

1. Make sure the **File Editor** add-on is installed in Home Assistant.
2. Open `configuration.yaml`.
3. Add a new `rest_command` entry, for example:

```yaml
rest_command:
  update_eink_screen:
    url: "https://api.switch-bot.com/v1.1/devices/YOUR_DEVICE_ID/commands"
    method: POST
    content_type: "application/json"
    headers:
      Authorization: "YOUR_TOKEN"
    payload: '{"command": "customPage", "commandType": "command", "parameter": "{{ message }} "}'
```

- Replace `YOUR_DEVICE_ID` with the Weather Station device ID from step 3.
- Replace `YOUR_TOKEN` with your API token from step 2.
- Use the boilerplate payload file for the exact command/parameter values.

4. Save the file.
5. Restart Home Assistant properly: **Settings > Developer Tools**, run **Check Configuration**, then restart.

# 5. Create an Automation to Trigger the Update

1. Go to **Settings > Automations & Scenes** and create a new automation.
2. Set whatever **trigger** you'd like the screen update to run on.
3. For the **action**, choose **Perform Action**, then select your `rest_command` (e.g. `rest_command.update_eink_screen`).
4. Pass in your message data/payload if prompted.
5. Save the automation, then run it manually once to test.

**Note:** It can take up to an hour for the E-Ink display to actually refresh after the command is sent.
