# Assignment 2 - Refactoring Based on Feedback

## Branch: `Refactor/A2feedback` 

## Overview
This document describes improvements made to A2 after receiving instructor feedback, before starting A3.

## Feedback Addressed

### 1. Requirements.txt Fixed
**Issue**: File contained unnecessary packages (black, etc.)  
**Fix**: 
- Cleaned to only `pygame==2.6.1`
- Add `requirements-dev.txt` for dev tools: `black` : code formatter 

### 2. Code Clarity Improvements
**Issue**: Monolithic `update()` method with magic numbers  
**Fixes**:
- Extracted helper methods: `_update_player()`, `_update_enemies()`, `_handle_coin_collision()`, `_handle_enemy_collision()`
- Added constants at top of `game.py` (removed magic numbers)
- Created `_load_media()` helper for sound loading

### 3. Spawn Robustness
**Issue**: Objects could spawn on top of player or each other  
**Fixes**:
- Coins spawn 100px+ away from player and avoid slow zone
- Slow zone spawns 150px+ away from player at start
- Enemies spawn 180px+ away from player (on start, level-up, and after losing life)
- New slow zone spawns 120px+ from player and 80px+ from coin on level-up

### 4. Level-up Feedback
**Issue**: Progression feedback was subtle  
**Fixes**:
- Added "LEVEL X!" visual message (2-second display with color fade)
- Added "Coins to next level: X" counter in HUD
- Added level-up sound effect
- Message draws on top of all game objects

### 5. Additional Audio Feedback
**Added sounds**:
- Coin collection sound
- Level-up sound
- Lost life sound
- Game over sound
- All organized in `assets/media/` folder
- Volume-balanced for good audio hierarchy

### 6. UI/UX Polish
**Fixes**:
- Draw order corrected so pause message appears on top of slow zone
- HUD expanded to show progression info
- Fair spawn system prevents frustrating instant deaths

## Code Structure Improvements

### Before:
- Single long `update()` method
- Magic numbers scattered throughout
- Sound loading mixed with initialization

### After:
- Clean separation: `_update_player()`, `_update_enemies()`, `_handle_coin_collision()`, `_handle_enemy_collision()`
- All constants defined at top
- Dedicated `_load_media()` method
- Helper methods for spawn validation

## Files Changed
- `src/game.py` - Major refactoring
- `requirements.txt` - Cleaned up
- Added `assets/media/` folder with 4 sound files
- Updated README.md (decision-change documentation improved)

## Testing Notes
- Player speed feels correct (360 normal / 133 in slow zone)
- Enemy spawns are fair (180px minimum distance)
- All sounds play at the system volume level
- Level progression is clear and rewarding
- Game doesn't break with missing sound files (graceful fallback)
