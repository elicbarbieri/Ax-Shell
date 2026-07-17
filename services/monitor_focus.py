from typing import Optional

from fabric.hyprland.widgets import get_hyprland_connection


class Signal:
    """Simple signal implementation for monitor focus service."""
    
    def __init__(self):
        self._callbacks = []
    
    def connect(self, callback):
        """Connect a callback to this signal."""
        self._callbacks.append(callback)
    
    def emit(self, *args, **kwargs):
        """Emit the signal to all connected callbacks."""
        for callback in self._callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Error in signal callback: {e}")


class MonitorFocusService:
    """
    Service to track monitor focus changes through Hyprland events.
    
    Listens to 'focusedmon' and 'workspace' events and emits signals
    when monitor focus changes.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._monitor_name_to_id = {}
        self._monitor_info = {}  # Store rich monitor information
        self._current_workspace = 1
        self._current_monitor_name = ""
        self._listening = False
        self._conn = None
        
        # Signals
        self.monitor_focused = Signal()
        self.workspace_changed = Signal()
        
        self._update_monitor_mapping()
        self.start_listening()
    
    def _update_monitor_mapping(self):
        """Update the monitor name to ID mapping with rich monitor information."""
        try:
            # Import here to avoid circular imports
            from utils.monitor_manager import get_monitor_manager
            manager = get_monitor_manager()
            monitors = manager.get_monitors()
            
            self._monitor_name_to_id = {}
            self._monitor_info = {}  # Store rich monitor information
            for monitor in monitors:
                monitor_name = monitor['name']
                monitor_id = monitor['id']
                self._monitor_name_to_id[monitor_name] = monitor_id
                self._monitor_info[monitor_id] = {
                    'name': monitor_name,
                    'width': monitor.get('width', 1920),
                    'height': monitor.get('height', 1080),
                    'x': monitor.get('x', 0),
                    'y': monitor.get('y', 0),
                    'scale': monitor.get('scale', 1.0),
                    'focused': monitor.get('focused', False)
                }
        except ImportError:
            # Fallback if monitor manager not available yet
            self._monitor_name_to_id = {}
            self._monitor_info = {}
    
    def start_listening(self):
        """Subscribe to Hyprland monitor/workspace events.

        We reuse fabric's shared Hyprland connection (the same one the bar,
        dock and overview use) rather than shelling out to `socat`. That drops
        the external `socat` dependency and, crucially, the hardcoded
        `/tmp/hypr/...` socket path, which has been wrong since Hyprland v0.40
        moved the IPC sockets to `$XDG_RUNTIME_DIR/hypr/`. fabric parses each
        socket2 line into a `HyprlandEvent` whose `.data` is the `>>`-payload
        split on commas.
        """
        if self._listening:
            return

        self._listening = True
        self._conn = get_hyprland_connection()
        self._conn.connect("event::focusedmon", self._on_focusedmon)
        self._conn.connect("event::workspace", self._on_workspace)

    def stop_listening(self):
        """Stop reacting to Hyprland events.

        fabric's connection is a process-global singleton shared with other
        widgets, so we don't tear it down; we just flip the flag that gates our
        handlers.
        """
        self._listening = False

    def _on_focusedmon(self, _conn, event):
        """focusedmon event: data = [monitor_name, workspace_name]."""
        if not self._listening or len(event.data) < 2:
            return
        try:
            self._handle_focused_monitor(event.data[0], event.data[1])
        except Exception as e:
            print(f"MonitorFocusService: Error in _on_focusedmon: {e}")

    def _on_workspace(self, _conn, event):
        """workspace event: data = [workspace_name]."""
        if not self._listening or not event.data:
            return
        try:
            self._handle_workspace_change(event.data[0])
        except Exception as e:
            print(f"MonitorFocusService: Error in _on_workspace: {e}")

    def _handle_focused_monitor(self, monitor_name: str, workspace_name: str):
        """Update state and emit for a monitor-focus change."""
        # Update monitor mapping if we've not seen this monitor yet.
        if monitor_name not in self._monitor_name_to_id:
            self._update_monitor_mapping()

        monitor_id = self._monitor_name_to_id.get(monitor_name, 0)

        try:
            workspace_id = int(workspace_name)
        except ValueError:
            workspace_id = 1

        self._current_monitor_name = monitor_name
        self._current_workspace = workspace_id

        self.monitor_focused.emit(monitor_name, monitor_id, workspace_id)

    def _handle_workspace_change(self, workspace_name: str):
        """Update state and emit for a workspace change."""
        try:
            workspace_id = int(workspace_name.strip())
        except ValueError:
            workspace_id = 1

        self._current_workspace = workspace_id
        self.workspace_changed.emit(workspace_id, self._current_monitor_name)
    
    def get_current_monitor_id(self) -> int:
        """Get current monitor ID."""
        return self._monitor_name_to_id.get(self._current_monitor_name, 0)
    
    def get_current_workspace(self) -> int:
        """Get current workspace ID."""
        return self._current_workspace
    
    def get_monitor_id_by_name(self, monitor_name: str) -> Optional[int]:
        """Get monitor ID by name."""
        return self._monitor_name_to_id.get(monitor_name)
    
    def get_monitor_info(self, monitor_id: int) -> Optional[dict]:
        """Get rich monitor information by ID."""
        return self._monitor_info.get(monitor_id)
    
    def get_current_monitor_info(self) -> Optional[dict]:
        """Get rich information for current monitor."""
        current_id = self.get_current_monitor_id()
        return self.get_monitor_info(current_id)
    
    def get_monitor_scale(self, monitor_id: int) -> float:
        """Get monitor scale factor by ID."""
        info = self.get_monitor_info(monitor_id)
        return info.get('scale', 1.0) if info else 1.0
    
    def get_current_monitor_scale(self) -> float:
        """Get current monitor scale factor."""
        return self.get_monitor_scale(self.get_current_monitor_id())


# Singleton accessor
_monitor_focus_service_instance = None

def get_monitor_focus_service() -> MonitorFocusService:
    """Get the global MonitorFocusService instance."""
    global _monitor_focus_service_instance
    if _monitor_focus_service_instance is None:
        _monitor_focus_service_instance = MonitorFocusService()
    return _monitor_focus_service_instance