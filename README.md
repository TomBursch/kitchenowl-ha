# KitchenOwl for Home Assistant

## Installation

This is not currently available in HACS, and the python package required is also not published on PyPi at the moment.
To manually install the integration in your local Home Assistant instance

1. Clone the repository locally
2. zip the `custom_components/kitchenowl` folder
3. Upload the zip to your instance to the `custom_components` folder
   - for example with the [File Editor Add-on](https://github.com/home-assistant/addons/tree/master/configurator)
4. Unzip the file
   - you can use the [Advanced SSH & Web Terminal Add-on](https://github.com/hassio-addons/addon-ssh) for this
   ```bash
   cd config/custom_compontents
   unzip kitchenowl.zip
   rm kitchenowl.zip
   ```
5. Restart Home Assistant
6. Set up the integration
   - Go to Settings > Devices & Services
   - Add Integration
7. Fill in your KitchenOwl settings
   - The IP / URL of your KitchenOwl instance
   - The Access Token (can be set up in your KitchenOwl Profile > Sessions)
8. Select the household

## Development

Set up the local development environment according to https://developers.home-assistant.io/docs/development_environment

### Clone this repo

### Mount the local directory

Add this to the `devcontainer.json` to mount your local directory into the container

```json
"mounts":[
    "source=<your_path>/custom_components,target=/workspaces/home-assistant-core/config/custom_components,type=bind,consistency=cached"
]
```
