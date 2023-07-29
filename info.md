# J-Tech Digital HDMI Matrix Integration for Home Assistant

## Features

The J-Tech Digital HDMI Matrix integration allows you to control and manage your J-Tech Digital HDMI Matrix directly from Home Assistant. The integration provides the following features:

- Media player support for each output in the HDMI matrix.
- Control over HDMI and CAT (Category) stream toggling for power efficiency.
- Sending CEC (Consumer Electronics Control) power commands to the source and output devices.
- Volume control options for modifying volume on the source or output.
- Integration with HomeKit TV remote key presses.

## Options

The J-Tech Digital HDMI Matrix integration offers the following customizable options:

- **Toggle HDMI Stream**: If enabled, the matrix will switch on and off the stream to HDMI outputs when the media player is turned on or off, optimizing power efficiency.

- **Toggle CAT Stream**: If enabled, the matrix will switch on and off the stream over CAT outputs when the media player is turned on or off, optimizing power efficiency.

- **Send CEC Power Commands to Source**: If enabled, the matrix will send power on and power off commands to the currently selected source (e.g., turning off the Apple TV when the media player is turned off).

- **Send CEC Power Commands to Output**: If enabled, the matrix will send power on and power off commands to the HDMI output (e.g., turning off the TV when the media player is turned off).

- **Delay (Stream Toggle to CEC Power)**: Used when "Send CEC Power Commands to Source" or "Send CEC Power Commands to Output" is enabled along with "Toggle HDMI Stream" or "Toggle CAT Stream." Adds a short delay between toggling the stream and sending the CEC power command.

- **Delay (CEC Power to Source)**: Used when "Send CEC Power Commands to Output" is enabled. Adds a short delay between sending the CEC power command and the subsequent "source" command (to output).

## Documentation

- Documentation: [GitHub - J-Tech Digital HDMI Matrix Integration](https://github.com/AlexOwl/jtechdigital-ha)

## Author

- Author: [@AlexOwl](https://github.com/AlexOwl)

## Support

For any support or inquiries, feel free to open an issue on the GitHub repository. Your feedback and contributions are welcome!
