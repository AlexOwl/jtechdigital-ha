# J-Tech Digital HDMI Matrix Integration for Home Assistant

## Features

The J-Tech Digital HDMI Matrix integration allows you to control and manage your J-Tech Digital HDMI Matrix directly from Home Assistant. The integration provides the following features:

- Media Player support for each output in the HDMI matrix.
- HDMI and CAT stream toggling for power efficiency.
- Sending CEC power commands to the source and output devices.
- Volume control options for modifying volume on the source or output.
- Integration with HomeKit TV remote key presses.

## Installation

To install the J-Tech Digital HDMI Matrix integration, follow these steps:

1. Add the custom repository to HACS:
   - Go to HACS in the Home Assistant web interface.
   - Click on Integrations.
   - Click on the three dots in the upper-right corner.
   - Select Custom repositories.
   - Enter the URL of the custom repository: `https://github.com/AlexOwl/jtechdigital-ha`.
   - Set the category to Integration.
   - Click the Add button.

2. Install the integration via HACS:
   - Go to HACS in the Home Assistant web interface.
   - Click on Integrations.
   - Click on the three dots in the upper-right corner.
   - Select Explore & Add Repositories.
   - Search for "J-Tech Digital HDMI Matrix" in the repository list.
   - Click Install for the J-Tech Digital HDMI Matrix integration.

3. Restart Home Assistant to apply the changes.

## Configuration

After installation, you can configure the J-Tech Digital HDMI Matrix integration via the Home Assistant web interface:

1. Go to Configuration > Integrations.
2. Click the Add Integration button.
3. Search for "J-Tech Digital HDMI Matrix" and select it.
4. Follow the on-screen instructions to set up the integration:
   - Enter the IP address or hostname of your J-Tech Digital HDMI Matrix.
   - Provide the username and password for authentication (default username and password can be changed on the device dashboard).
   - Confirm the setup.

## Options

The J-Tech Digital HDMI Matrix integration offers the following customizable options:

- **Toggle HDMI Stream**: If enabled, the matrix will switch on and off the stream to HDMI outputs when the media player is turned on or off, optimizing power efficiency.

- **Toggle CAT Stream**: If enabled, the matrix will switch on and off the stream over CAT outputs when the media player is turned on or off, optimizing power efficiency.

- **Send CEC Power Commands to Source**: If enabled, the matrix will send power on and power off commands to the currently selected source (e.g., turning off the Apple TV when the media player is turned off).

- **Send CEC Power Commands to Output**: If enabled, the matrix will send power on and power off commands to the HDMI output (e.g., turning off the TV when the media player is turned off).

- **Delay (Stream Toggle to CEC Power)**: Used when "Send CEC Power Commands to Source" or "Send CEC Power Commands to Output" is enabled along with "Toggle HDMI Stream" or "Toggle CAT Stream." Adds a short delay between toggling the stream and sending the CEC power command.

- **Delay (CEC Power to Source)**: Used when "Send CEC Power Commands to Output" is enabled. Adds a short delay between sending the CEC power command and the subsequent "source" command (to output).

## Documentation and Issue Tracker

- Documentation: [GitHub - J-Tech Digital HDMI Matrix Integration](https://github.com/AlexOwl/jtechdigital-ha)
- Issue Tracker: [GitHub Issues - J-Tech Digital HDMI Matrix Integration](https://github.com/AlexOwl/jtechdigital-ha/issues)

## Author

- Author: [@AlexOwl](https://github.com/AlexOwl)

## Support

For any support or inquiries, feel free to open an issue on the GitHub repository. Your feedback and contributions are welcome!
