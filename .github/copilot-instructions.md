# Copilot Instructions for Desk Control API

## Architecture Overview
This is a FastAPI-based REST API for controlling an IKEA standing desk via Bluetooth Low Energy (BLE). The app follows a modular structure under `apps/desk/` with clear separation of concerns:

- **API Layer** (`apps/desk/api/`): FastAPI routers for endpoints like `/desk/height` and `/desk/preset`
- **Service Layer** (`apps/desk/services/`): Business logic coordinating state and hardware operations
- **Driver Layer** (`apps/desk/drivers/`): BLE communication using the `bleak` library
- **Core** (`apps/desk/core/`): Configuration (pydantic-settings), global state management, and logging
- **Models** (`apps/desk/models/`): Pydantic request/response models with validation

Data flows from API → Service → Driver → BLE desk. State is managed globally in `apps/desk/core/state.py`.

## Key Patterns
- **Height Conversion**: Desk reports raw values; convert using `raw_to_mm(raw) = (raw // 10) + 620` and `mm_to_raw(mm) = (mm - 620) * 10`. See `apps/desk/drivers/desk_driver.py`.
- **BLE Commands**: Use `struct.pack("<H", value)` for command bytearrays. Examples: `COMMAND_UP = bytearray(struct.pack("<H", 71))`. Reference UUIDs in `desk_driver.py`.
- **Async Operations**: All desk movements are async. Use `asyncio.create_task()` for fire-and-forget operations like `desk_service.set_height(height)`.
- **Configuration**: Settings from environment variables with `DESK_` prefix (e.g., `DESK_MAC_ADDRESS`). Fallback to `apps/desk/core/config.py`. Height bounds: min 600mm, max 1400mm.
- **State Management**: Global `desk_state` and `presets` objects. Update state in callbacks from BLE notifications.
- **Error Handling**: BLE operations may fail; wrap in try/except with `BleakError`. Use timeouts from config.

## Developer Workflows
- **Run Locally**: `python main.py` starts FastAPI with uvicorn reload. Access docs at `http://localhost:8000/docs`.
- **BLE Setup**: Requires Bluetooth adapter. MAC address configured in `desk_config.json` or env var. Test with real IKEA desk hardware.
- **Debugging**: Monitor BLE connection logs via `apps/desk/core/logger.py`. Check desk state via GET `/desk/`.
- **Dependencies**: Install with `pip install -e .` (uses `pyproject.toml`). Requires Python >=3.12.

## Conventions
- Import paths: Always use absolute imports like `from apps.desk.core.config import settings`.
- Logging: Use `logger = logger.get_logger(__name__)` from `apps/desk/core/logger.py`.
- Validation: Pydantic models enforce height ranges using `settings.min_height` and `settings.max_height`.
- Presets: Stored in `apps/desk/core/state.py` as dict of `Preset` objects with name and height.

Reference `desk.py` (root) for low-level BLE operations, but prefer the service/driver abstraction for new features.