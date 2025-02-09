# KitchenOwl for Home Assistant

An alpha version [KitchenOwl](https://kitchenowl.org) Home Assistant integration.

The integration currently supports:
- Adding and removing shopping list items

## Installation

### Using HACS
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TomBursch&repository=kitchenowl-ha&category=integration)

### Manually

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

## Configuration

1. Set up the integration
   - Go to Settings > Devices & Services
   - Add Integration
2. Fill in your KitchenOwl settings
   - The IP / URL of your KitchenOwl instance (If you're using the KitchenOwl cloud enter `https://app.kitchenowl.org`)
   - The Access Token (can be set up in KitchenOwl by going to Profile -> Sessions)
3. Select the household

## Development

Set up the local development environment according to https://developers.home-assistant.io/docs/development_environment

### Clone this repo

### Mount the local directory

Add this to the `devcontainer.json` to mount your local directory into the container

```json
"mounts":[
    "source=<your_path>/custom_components,target=/workspaces/core/config/custom_components,type=bind,consistency=cached"
]
```
