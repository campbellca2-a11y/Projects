# Mouse Distance Tracker 🖱️

A fun web application that tracks the total distance your mouse travels and visualizes it through creative "Perspective Capsules" - comparing your mouse journey to real-world distances.

## Features

### Distance Tracking
- **Real-time tracking** of mouse movement distance
- **Automatic conversion** from pixels to real-world units (meters, kilometers)
- **Persistent storage** - your total distance is saved and continues across sessions
- **Session tracking** - see how far you've traveled in the current session
- **Speed calculation** - monitor your current mouse movement speed

### Perspective Capsules

The app includes 8 unique perspective capsules that help you visualize your mouse distance:

1. **🌙 Journey to the Moon** - 384,400 km to the Moon
2. **🌍 Around the Earth** - 40,075 km circumference at the equator
3. **🏔️ Climbing Mount Everest** - 8,849 m tall
4. **🏯 The Great Wall of China** - 21,196 km total length
5. **🏃 Marathon Distance** - 42.195 km official race distance
6. **🗼 Eiffel Tower Height** - 330 m including antenna
7. **⚽ Football Field** - 91.44 m American football field length
8. **🌊 Mariana Trench** - 10,994 m deepest point in Earth's oceans

Each capsule shows:
- Progress percentage toward the goal
- Number of times you've completed the distance
- Remaining distance to reach the goal
- Visual progress bar with custom colors

## How to Use

1. **Open** `index.html` in your web browser
2. **Move your mouse** anywhere on the page to start tracking
3. **Watch** your distance accumulate in real-time
4. **View** your progress across different perspective capsules
5. **Reset** your total distance or session distance using the buttons

## Technical Details

### Distance Calculation
- Tracks mouse movement in pixels
- Converts pixels to inches using standard web DPI (96 pixels/inch)
- Converts inches to meters for accurate real-world measurements
- Uses Pythagorean theorem to calculate distance: `√(dx² + dy²)`

### Data Persistence
- Uses `localStorage` to save your total distance
- Data persists across browser sessions
- Automatic saving on every mouse movement

### Speed Calculation
- Calculates instantaneous speed based on distance and time
- Averages over the last 10 movement samples for smooth display
- Updates 10 times per second

## Browser Compatibility

Works in all modern browsers:
- Chrome/Edge
- Firefox
- Safari
- Opera

## Installation

No installation required! Simply:

1. Clone or download the repository
2. Open `index.html` in your browser
3. Start moving your mouse

## Files

- `index.html` - Main HTML structure
- `styles.css` - Styling and visual design
- `app.js` - Core tracking logic and perspective capsules
- `README.md` - This file

## Customization

### Adding New Perspective Capsules

Edit the `capsules` array in `app.js` (around line 108):

```javascript
{
    id: 'custom',
    icon: '🎯',
    title: 'Your Custom Distance',
    description: 'Description of the distance',
    targetDistance: 1000, // in meters
    color: '#ff6b6b'
}
```

### Adjusting DPI

If your display has a different DPI, modify line 10 in `app.js`:

```javascript
this.pixelsPerInch = 96; // Change to your screen's DPI
```

## Fun Facts

- Moving your mouse in small circles is more efficient for racking up distance
- The average person moves their mouse about 1-2 km per day
- Reaching the Moon would take approximately 500+ years of normal mouse usage
- Gamers can achieve 5-10 km per day during intense gaming sessions

## Future Enhancements

Potential features to add:
- More perspective capsules (Mars, ISS orbit, etc.)
- Daily/weekly/monthly statistics
- Achievement system with badges
- Comparison with other users
- Export data as JSON/CSV
- Dark mode toggle
- Custom capsule creator

## Contributing

Feel free to fork and add your own perspective capsules or features!

## License

MIT License - Feel free to use and modify as you wish.

---

**Enjoy tracking your mouse journey! 🚀**
