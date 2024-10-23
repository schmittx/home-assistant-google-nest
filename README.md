[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
# Google Nest Home Assistant Integration
Custom component to allow control of [Google Nest](https://home.nest.com) devices in [Home Assistant](https://home-assistant.io).

## Credit
- This is heavily based on [@iMicknl's repo](https://github.com/iMicknl/ha-nest-protect), but with additional entities and support for more Google Nest devices.

## Notes
- This integration only supports Google accounts (no Nest accounts).

## Install
1. Ensure Home Assistant is updated to version 2024.10.0 or newer.
2. Use HACS and add as a [custom repo](https://hacs.xyz/docs/faq/custom_repositories); or download and manually move to the `custom_components` folder.
3. Once the integration is installed follow the standard process to setup via UI and search for `Google Nest`.
4. Follow the prompts.

## Supported Devices
- Nest Cam (1st Generation)
- Nest Cam IQ
- Nest Doorbell (1st Generation)
- Nest Protect
- Nest Temperature Sensor
- Nest Thermostat (3rd Generation)