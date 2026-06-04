# VK Teams Integration Plugin

## Overview
This plugin provides integration with VK Teams corporate messenger for Hermes Agent.
It enables sending messages, files, and managing interactions within VK Teams channels.

## Configuration
Add the following to your `config.yaml`:

```yaml
vkteams:
  require_mention: true
  # Add other VK Teams specific settings here as needed
```

## Features
- **Message Sending**: Send text and rich messages to VK Teams chats.
- **File Upload**: Support for uploading documents and images.
- **Mention Handling**: Automatic detection of @mentions for bot activation.

## Usage
The agent will automatically load this skill when connected to a VK Teams session.
No additional commands are required for basic operation.
