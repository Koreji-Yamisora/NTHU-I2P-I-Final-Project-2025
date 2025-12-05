.. NTHU I2P Final Project documentation master file

Pokemon Battle Game Documentation
===================================

A Pokemon-style game built with Pygame featuring turn-based combat, wild encounters, 
trainer battles, and a comprehensive item system with stat-boosting mechanics.

.. image:: https://img.shields.io/badge/python-3.12.8-blue
   :alt: Python 3.12.8
   :target: https://www.python.org/

.. image:: https://img.shields.io/badge/pygame-2.x-green
   :alt: Pygame

Features
--------
**Turn-Based Combat System**
   Speed-based initiative with Pokemon-accurate battle mechanics

**Comprehensive Item System**
   - Healing potions (restore HP)
   - Stat-boosting items (X Attack, X Defense, etc.)
   - Pokeballs for catching wild Pokemon

**Wild Encounters**
   Battle and catch Pokemon in the wild with varying catch rates

**Trainer Battles**
   Challenge AI trainers with strategic turn-based combat

**Map Exploration**
   Navigate through different areas with teleportation and NPCs

**Save/Load System**
   Persistent game state with multiple save slots

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/Koreji-Yamisora/NTHU-I2P-I-Final-Project-2025.git
   cd NTHU-I2P-I-Final-Project-2025

   # Install dependencies (using uv)
   uv sync

   # Run the game
   uv run python main.py

Gameplay Basics
~~~~~~~~~~~~~~~

**Controls:**

- Arrow Keys: Move player
- ESC: Open settings menu
- Enter/Space: Interact with NPCs/objects

**Combat:**

1. Select action (Fight/Bag/Pokemon/Run)
2. Choose move or item
3. Actions execute based on speed
4. Defeat enemy to win!

Architecture Overview
---------------------

The game follows a modular architecture with clear separation of concerns:

.. code-block:: text

   NTHU Pokemon Game
   │
   ├── Core Systems (src/core/)
   │   ├── Engine
   │   │   └── Main game loop (60 FPS)
   │   │
   │   ├── Managers (src/core/managers/)
   │   │   ├── GameManager - Game state & save/load
   │   │   ├── SceneManager - Scene transitions
   │   │   ├── SoundManager - Background music & SFX
   │   │   ├── InputManager - Keyboard/mouse input
   │   │   ├── ResourceManager - Asset loading & caching
   │   │   └── OnlineManager - Multiplayer (future)
   │   │
   │   └── Services
   │       └── Global service access points
   │
   ├── Combat System (src/scenes/)
   │   ├── CombatScene (Base Framework)
   │   │   ├── Turn-based system
   │   │   ├── Speed-based initiative
   │   │   ├── Stat stage tracking (-6 to +6)
   │   │   ├── Move execution
   │   │   └── Item usage
   │   │
   │   ├── EncounterScene (Wild Battles)
   │   │   ├── Wild Pokemon encounters
   │   │   ├── Catching mechanics
   │   │   └── Escape/run logic
   │   │
   │   └── BattleScene (Trainer Battles)
   │       ├── Trainer AI
   │       ├── Forced battles
   │       └── Victory/defeat handling
   │
   ├── Entities (src/entities/)
   │   ├── Entity (Base Class)
   │   │   ├── Position & movement
   │   │   ├── Collision detection
   │   │   └── Animation handling
   │   │
   │   ├── Player
   │   │   ├── Keyboard controls
   │   │   ├── Auto-walk pathfinding (BFS)
   │   │   ├── Teleport zones
   │   │   └── Bush interactions
   │   │
   │   ├── NPC
   │   │   ├── Line-of-sight detection
   │   │   ├── Shop interactions
   │   │   └── Dialogue system
   │   │
   │   └── EnemyTrainer
   │       ├── LOS-based detection
   │       ├── Battle initiation
   │       └── Trainer AI
   │
   ├── UI System (src/interface/)
   │   ├── Components (src/interface/components/)
   │   │   ├── Overlay (Base class)
   │   │   ├── Button (Interactive buttons)
   │   │   ├── Slider (Volume controls)
   │   │   └── ToggleButton (Settings)
   │   │
   │   ├── Combat Overlays (overlay_combat.py)
   │   │   ├── ActionOverlay - Fight/Bag/Pokemon/Run
   │   │   ├── MoveOverlay - Move selection
   │   │   ├── ItemOverlay with Inventory display
   │   │   ├── SwitchOverlay - Pokemon switching
   │   │   ├── HealthOverlay - HP bars & stats
   │   │   └── Victory - Battle results
   │   │
   │   ├── Game Overlays (overlay_game.py)
   │   │   ├── SettingOverlay - Volume/save/load
   │   │   └── Inventory - Pokemon & items
   │   │
   │   └── Shop Overlay (overlay_shop.py)
   │       └── NPC shop interface
   │
   ├── Data Management (src/data/)
   │   ├── Pokedex
   │   │   ├── Pokemon species data
   │   │   ├── Type effectiveness
   │   │   └── Move database
   │   │
   │   └── Bag
   │       ├── Pokemon party (max 6)
   │       ├── Item inventory
   │       ├── Pokeballs
   │       └── Stat-boosting items
   │
   ├── Map System (src/maps/)
   │   ├── Map
   │   │   ├── Tiled TMX loading
   │   │   ├── Collision layers
   │   │   ├── Teleport zones
   │   │   ├── Warp points
   │   │   └── NPC spawning
   │   │
   │   └── Camera
   │       └── Viewport tracking player
   │
   ├── Rendering (src/sprites/)
   │   ├── Sprite - Static images
   │   ├── Animation - Frame-based animation
   │   └── Background - Parallax backgrounds
   │
   └── Utilities (src/utils/)
       ├── Position & PositionCamera - 2D coordinates
       ├── Direction - UP/DOWN/LEFT/RIGHT enum
       ├── GameSettings - Constants & config
       ├── Logger - Debug logging
       └── Color utilities - Sprite tinting

Combat System
~~~~~~~~~~~~~

The combat system uses a **speed-based turn order**:

1. Both player and enemy select actions
2. Turn queue is built with priorities:
   - Priority 1: Items, switching (always first)
   - Priority 0: Moves (ordered by Speed stat)
3. Actions execute in order
4. Damage is calculated with stat stage multipliers
5. Check for faints and handle switches

**Stat Stages:**

- Range: -6 to +6
- Multipliers: 0.25x (stage -6) to 4.0x (stage +6)
- Reset after battle ends

Documentation Contents
----------------------

.. note::
   This is a single-page documentation. All content is on this page for easy navigation.

Module Reference
----------------

Core Modules
~~~~~~~~~~~~

- :mod:`src.core.engine` - Game engine and main loop
- :mod:`src.core.managers` - Core managers (scene, sound, input, etc.)
- :mod:`src.scenes` - Game scenes (combat, menu, etc.)
- :mod:`src.entities` - Game entities (player, NPCs, trainers)
- :mod:`src.interface` - UI components and overlays
- :mod:`src.data` - Data management (Pokemon, items, etc.)

Key Classes
~~~~~~~~~~~

**Combat:**

- :class:`src.scenes.combat.CombatScene` - Unified combat framework
- :class:`src.scenes.encounter_scene.EncounterScene` - Wild encounters
- :class:`src.scenes.battle_scene.BattleScene` - Trainer battles

**Entities:**

- :class:`src.entities.player.Player` - Player character
- :class:`src.entities.npc.Npc` - Non-player characters
- :class:`src.entities.enemy_trainer.EnemyTrainer` - Enemy trainers

**Managers:**

- :class:`src.core.managers.game_manager.GameManager` - Game state
- :class:`src.core.managers.scene_manager.SceneManager` - Scene transitions
- :class:`src.core.managers.sound_manager.SoundManager` - Audio



Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd docs
   make html
   # View at docs/_build/html/index.html


Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
=======

This project was created for NTHU Introduction to Programming I Final Project (2025).

**Author:** Chen Wenxin

**Version:** 0.5
