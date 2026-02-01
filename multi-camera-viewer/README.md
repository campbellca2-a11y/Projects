# Multi-Camera RTSP Viewer

A simple web-based viewer for displaying multiple RTSP camera feeds simultaneously in your browser.

## How It Works

Browsers cannot play RTSP streams directly. This solution uses **go2rtc**, a lightweight media server that converts RTSP streams to browser-friendly formats (MSE/WebRTC).

```
RTSP Cameras → go2rtc (converts streams) → Browser (viewer.html)
```

## Quick Start

### 1. Download go2rtc

Download the appropriate binary for your system from:
https://github.com/AlexxIT/go2rtc/releases

| OS | File |
|----|------|
| Windows | `go2rtc_win64.zip` |
| macOS (Intel) | `go2rtc_mac_amd64.zip` |
| macOS (Apple Silicon) | `go2rtc_mac_arm64.zip` |
| Linux | `go2rtc_linux_amd64` |

Extract and place the binary in this folder.

### 2. Configure Your Cameras

Edit `go2rtc.yaml` and replace the placeholder RTSP URLs with your actual camera URLs:

```yaml
streams:
  camera1:
    - rtsp://username:password@192.168.1.101:554/stream1
  camera2:
    - rtsp://username:password@192.168.1.102:554/stream1
  camera3:
    - rtsp://username:password@192.168.1.103:554/stream1
```

**Finding your RTSP URL:**
- Check your camera's manual or admin interface
- Common formats:
  - `rtsp://user:pass@IP:554/stream1`
  - `rtsp://user:pass@IP:554/h264`
  - `rtsp://user:pass@IP:554/cam/realmonitor?channel=1&subtype=0`

### 3. Start go2rtc

**Windows:**
```cmd
go2rtc.exe -config go2rtc.yaml
```

**macOS/Linux:**
```bash
./go2rtc -config go2rtc.yaml
```

You should see output indicating the streams are connected.

### 4. Open the Viewer

Open `viewer.html` in your web browser (Chrome, Firefox, Edge, Safari).

Or access go2rtc's built-in UI at: http://localhost:1984

## Troubleshooting

### "Unable to load camera feed" error

1. **Check go2rtc is running** - You should see it in your terminal
2. **Verify RTSP URLs** - Test with VLC first to confirm they work
3. **Check firewall** - Ensure ports 1984 and 8554 are accessible
4. **Check camera credentials** - Username/password in the URL

### Streams are laggy

- Use the sub-stream (lower resolution) for multi-camera viewing
- Check your network bandwidth
- go2rtc uses MSE by default; WebRTC has lower latency but may have compatibility issues

### Browser shows black video

- Click on the video to unmute/play (some browsers block autoplay)
- Try a different browser
- Check browser console (F12) for errors

## Advanced Configuration

### Using WebRTC (Lower Latency)

Edit `viewer.html` and change the stream URL from:
```javascript
const streamUrl = `${config.serverUrl}/api/stream.mp4?src=${camera.name}`;
```
to:
```javascript
const streamUrl = `${config.serverUrl}/api/webrtc?src=${camera.name}`;
```

Note: WebRTC requires additional setup for the video element.

### Running on a Different Port

Edit `go2rtc.yaml`:
```yaml
api:
  listen: ":8080"  # Change to desired port
```

Then update the server URL in the viewer's settings.

### Running as a Service

**Linux (systemd):**

Create `/etc/systemd/system/go2rtc.service`:
```ini
[Unit]
Description=go2rtc
After=network.target

[Service]
ExecStart=/path/to/go2rtc -config /path/to/go2rtc.yaml
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable go2rtc
sudo systemctl start go2rtc
```

**Windows:**

Use Task Scheduler to run go2rtc at startup.

## Files

- `viewer.html` - The web-based multi-camera viewer
- `go2rtc.yaml` - Configuration file for go2rtc
- `README.md` - This file

## Requirements

- go2rtc (download from GitHub)
- A modern web browser (Chrome, Firefox, Edge, Safari)
- Network access to your RTSP cameras

## Resources

- [go2rtc GitHub](https://github.com/AlexxIT/go2rtc) - Full documentation
- [go2rtc Wiki](https://github.com/AlexxIT/go2rtc/wiki) - Configuration examples
