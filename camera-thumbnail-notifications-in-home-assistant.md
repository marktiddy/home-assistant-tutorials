# Camera Thumbnail Notifications in Home Assistant

**Support my work:** https://buymeacoffee.com/marktiddy

## Requirements

Before you start, you'll need:

- Home Assistant
- A camera integrated with Home Assistant
- A motion sensor (either from the camera or a separate sensor)
- The Home Assistant mobile app configured on your phone
- Remote access configured (recommended), using either:
  - Home Assistant Cloud, or
  - Cloudflare Tunnels

This guide will create a notification with a camera thumbnail on your phone and Apple Watch when motion is detected.

---

## 1. Create a New Automation

Go to:

**Settings → Automations & Scenes → Create Automation**

---

## 2. Configure the Trigger

Set the trigger to your motion sensor.

For example, some cameras expose multiple motion types such as:

- Person
- Animal
- Vehicle

Select whichever motion entity you want to trigger notifications.

---

## 3. Add an Anti-Spam Condition

Add an **And If** condition and choose **Template**.

Replace the automation name with the name you plan to save your automation as:

```jinja
{{ as_timestamp(now()) - as_timestamp(state_attr('automation.human_garden_detected', 'last_triggered'), 0) > 30 }}
```

This prevents the automation from running more than once every 30 seconds.

Change `30` to any number of seconds you prefer.

> Optional: Add another condition to only send notifications when nobody is home.

---

## 4. Take a Camera Snapshot

Add a **Take Snapshot** action.

Configure:

- **Camera:** Your camera entity
- **Filename:**

```text
/media/human.jpg
```

You can use any filename or create subfolders if required.

---

## 5. Send the Mobile Notification

Add a **Send Notification via Mobile App** action.

Select your device and enter your notification message.

In the **Data** section, add:

```yaml
image: /media/local/human.jpg
```

> Note: `/media/local/` provides public access to files stored in the `/media/` folder.

Example:

```yaml
title: Person Detected
message: Motion detected in the garden
data:
  image: /media/local/human.jpg
```

---

## 6. Save and Test

Save the automation using the same name referenced in the template condition.

For example:

```text
Human Garden Detected
```

Then select **Run Actions** to test the notification.

That's it — you should now receive camera thumbnail notifications on your phone and Apple Watch.

---

**Support my work:** https://buymeacoffee.com/marktiddy
