from typing import Dict, List, Optional, Union, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import gi

gi.require_version("GObject", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Wp", "0.5")

from gi.repository import GObject, GLib, Wp

# ========== LEGACY DATA STRUCTURES (for API compatibility) ==========


class NodeState(Enum):
    """WirePlumber node states"""

    ERROR = "error"
    CREATING = "creating"
    SUSPENDED = "suspended"
    IDLE = "idle"
    RUNNING = "running"


class PortDirection(Enum):
    """Port direction enumeration"""

    INPUT = "in"
    OUTPUT = "out"


@dataclass
class ApplicationInfo:
    """Application-specific node information"""

    name: str  # application.name
    pid: int  # application.process.id
    binary: str  # application.process.binary
    icon: Optional[str] = None  # application.icon_name


@dataclass
class DeviceHardwareInfo:
    """Hardware device information"""

    api: str  # device.api (alsa, bluez5, etc.)
    class_: str  # device.class (sound, etc.)
    bus: Optional[str] = None  # device.bus (pci, usb, bluetooth)
    vendor: Optional[str] = None  # device.vendor
    product: Optional[str] = None  # device.product


@dataclass
class AudioPort:
    """Audio port information"""

    id: int  # object.id
    name: str  # port.name
    direction: PortDirection  # port.direction
    alias: Optional[str] = None  # port.alias
    audio_channel: Optional[str] = None  # audio.channel
    node_id: int = 0  # Associated node ID


@dataclass
class DeviceProfile:
    """Device profile (analog-stereo, pro-audio, etc.)"""

    name: str  # Profile name
    description: str  # Human-readable description
    priority: int = 0  # Profile priority
    available: bool = True  # Profile availability


@dataclass
class DeviceRoute:
    """Device route (headphones, speakers, line-out)"""

    name: str  # Route name
    description: str  # Human-readable description
    direction: PortDirection  # Route direction
    priority: int = 0  # Route priority
    available: bool = True  # Route availability


@dataclass
class AudioNodeInfo:
    """Complete audio node information"""

    id: int  # WirePlumber node ID
    name: str  # node.name
    description: str  # node.description
    media_class: str  # media.class (Audio/Sink, Stream/Output/Audio)
    volume: float = 0.0  # Current volume (0.0-1.0)
    muted: bool = False  # Current mute state
    channels: int = 2  # Number of channels
    sample_rate: int = 48000  # Current sample rate
    state: NodeState = NodeState.IDLE
    device_id: Optional[int] = None  # Parent device ID
    application: Optional[ApplicationInfo] = None  # For stream nodes
    device: Optional[DeviceHardwareInfo] = None  # For device nodes
    ports: List[AudioPort] = field(default_factory=list)
    is_default: bool = False  # Is default sink/source
    nick: Optional[str] = None  # node.nick (user-friendly name)


@dataclass
class AudioDeviceInfo:
    """Complete audio device information"""

    id: int  # Device ID
    name: str  # device.name
    description: str  # device.description
    api: str  # device.api
    class_: str  # device.class
    nick: Optional[str] = None  # device.nick
    profiles: List[DeviceProfile] = field(default_factory=list)
    active_profile: Optional[DeviceProfile] = None
    routes: List[DeviceRoute] = field(default_factory=list)
    active_route: Optional[DeviceRoute] = None
    node_ids: List[int] = field(default_factory=list)  # Associated nodes


@dataclass
class VolumeInfo:
    """Volume and mute state information"""

    volume: float  # Volume level (0.0-1.0)
    muted: bool  # Mute state
    channels: int = 2  # Number of channels


@dataclass
class AudioLink:
    """Audio connection between nodes"""

    id: int  # Link ID
    output_node_id: int  # Source node ID
    input_node_id: int  # Target node ID
    output_port_id: Optional[int] = None  # Specific output port
    input_port_id: Optional[int] = None  # Specific input port


@dataclass
class AudioGraph:
    """Complete PipeWire audio graph"""

    nodes: List[AudioNodeInfo] = field(default_factory=list)
    devices: List[AudioDeviceInfo] = field(default_factory=list)
    links: List[AudioLink] = field(default_factory=list)
    default_sink_id: Optional[int] = None
    default_source_id: Optional[int] = None


@dataclass
class VirtualDeviceConfig:
    """Configuration for creating virtual audio devices"""

    name: str  # node.name
    description: Optional[str] = None  # node.description
    channels: int = 2  # audio.channels
    sample_rate: int = 48000  # audio.rate
    channel_map: Optional[str] = None  # audio.position (e.g., "FL,FR")
    passive: bool = False  # node.passive
    media_class: Optional[str] = None  # media.class override


# Convenience type aliases for common use cases
SinkInfo = AudioNodeInfo  # Output device/node
SourceInfo = AudioNodeInfo  # Input device/node
StreamInfo = AudioNodeInfo  # Application stream

# ========== CORE REACTIVE AUDIO NODE ==========


class AudioNode(GObject.Object):
    """
    Individual audio node with reactive properties.

    Widgets bind directly to these properties:
    - volume_slider.bind_property(node, 'volume')
    - mute_button.bind_property(node, 'muted')
    """

    __gtype_name__ = "AudioNode"

    # Properties automatically emit notify signals when changed
    node_id = GObject.Property(type=int, flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    name = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    description = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    media_class = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    volume = GObject.Property(type=float, default=0.0, minimum=0.0, maximum=1.0, flags=GObject.ParamFlags.READWRITE)
    muted = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    is_default = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, node_id: int, service: "AudioService"):
        super().__init__(node_id=node_id)
        self._service = service

        # Connect to our own property changes to forward to WirePlumber
        self.connect("notify::volume", self._on_volume_changed)
        self.connect("notify::muted", self._on_muted_changed)

    def _on_volume_changed(self, obj, pspec):
        """Forward volume changes to WirePlumber (async safe)"""
        self._service._set_wp_volume(self.node_id, self.volume)

    def _on_muted_changed(self, obj, pspec):
        """Forward mute changes to WirePlumber (async safe)"""
        self._service._set_wp_mute(self.node_id, self.muted)

    # Convenience methods for widgets
    def toggle_mute(self) -> None:
        """Toggle mute state (triggers property change)"""
        self.muted = not self.muted

    def set_volume_percent(self, percent: int) -> None:
        """Set volume from percentage (0-100)"""
        self.volume = max(0.0, min(1.0, percent / 100.0))

    def get_volume_percent(self) -> int:
        """Get volume as percentage for UI display"""
        return int(self.volume * 100)


# ========== REACTIVE NODE COLLECTION ==========


class NodeCollection(GObject.Object):
    """
    Collection of AudioNodes that emits signals when nodes are added/removed.

    Widgets can connect to 'node-added'/'node-removed' signals for live updates.
    """

    __gtype_name__ = "NodeCollection"

    __gsignals__ = {
        "node-added": (GObject.SignalFlags.RUN_FIRST, None, (AudioNode,)),
        "node-removed": (GObject.SignalFlags.RUN_FIRST, None, (int,)),  # node_id
        "nodes-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self._nodes: Dict[int, AudioNode] = {}

    def add_node(self, node: AudioNode) -> None:
        """Add node and emit signal"""
        self._nodes[node.node_id] = node
        self.emit("node-added", node)
        self.emit("nodes-changed")

    def remove_node(self, node_id: int) -> bool:
        """Remove node and emit signal"""
        if node_id in self._nodes:
            del self._nodes[node_id]
            self.emit("node-removed", node_id)
            self.emit("nodes-changed")
            return True
        return False

    def get_node(self, node_id: int) -> Optional[AudioNode]:
        """Get node by ID"""
        return self._nodes.get(node_id)

    def get_nodes(self) -> List[AudioNode]:
        """Get all nodes as list"""
        return list(self._nodes.values())

    def __len__(self) -> int:
        return len(self._nodes)


# ========== MAIN REACTIVE AUDIO SERVICE ==========


class AudioService(GObject.Object):
    """
    Minimal reactive audio service optimized for real-time widgets.

    Usage:
        service = AudioService()

        # Get reactive collections
        sinks = service.sinks
        sources = service.sources

        # Connect to live updates
        sinks.connect('node-added', on_sink_added)

        # Bind widget to individual node
        node = sinks.get_node(123)
        volume_slider.bind_property('value', node, 'volume', BIDIRECTIONAL)
    """

    __gtype_name__ = "AudioService"

    __gsignals__ = {
        "connected": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "disconnected": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "default-sink-changed": (GObject.SignalFlags.RUN_FIRST, None, (AudioNode,)),
        "default-source-changed": (GObject.SignalFlags.RUN_FIRST, None, (AudioNode,)),
        "devices-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "streams-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "volume-changed": (GObject.SignalFlags.RUN_FIRST, None, (int, float, bool)),
        "stream-added": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "stream-removed": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "profile-changed": (GObject.SignalFlags.RUN_FIRST, None, (int, object)),
        "connection-state-changed": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    # Service-level reactive properties
    connected = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READABLE)
    default_sink = GObject.Property(type=AudioNode, flags=GObject.ParamFlags.READABLE)
    default_source = GObject.Property(type=AudioNode, flags=GObject.ParamFlags.READABLE)

    # Legacy properties for compatibility
    sinks = GObject.Property(type=object, default=None)
    sources = GObject.Property(type=object, default=None)
    sink_inputs = GObject.Property(type=object, default=None)
    source_outputs = GObject.Property(type=object, default=None)
    default_sink_volume = GObject.Property(type=float, default=0.0)
    default_source_volume = GObject.Property(type=float, default=0.0)
    default_sink_muted = GObject.Property(type=bool, default=False)
    default_source_muted = GObject.Property(type=bool, default=False)
    devices = GObject.Property(type=object, default=None)
    audio_graph = GObject.Property(type=object, default=None)

    def __init__(self):
        super().__init__()

        # Reactive collections for different node types
        self.sinks = NodeCollection()  # Output devices
        self.sources = NodeCollection()  # Input devices
        self.streams = NodeCollection()  # Application streams

        # WirePlumber state
        self._wp_core: Optional[Wp.Core] = None
        self._mixer_api: Optional[object] = None  # WpPlugin for mixer-api
        self._defaults_api: Optional[object] = None  # WpPlugin for default-nodes-api
        self._wp_nodes: Dict[int, Wp.Node] = {}
        self._object_manager: Optional[Wp.ObjectManager] = None
        self._pending_plugins = 0
        self._required_plugins = ["mixer-api", "default-nodes-api"]

        # Legacy compatibility state
        self._is_ready = False
        self._connection_failed = False
        self._nodes: Dict[int, Wp.Node] = {}
        self._devices: Dict[int, Wp.Device] = {}
        self._node_info: Dict[int, AudioNodeInfo] = {}
        self._device_info: Dict[int, AudioDeviceInfo] = {}
        self._default_sink_id: Optional[int] = None
        self._default_source_id: Optional[int] = None

        # Initialize legacy properties
        self.props.sinks = []
        self.props.sources = []
        self.props.sink_inputs = []
        self.props.source_outputs = []
        self.props.devices = []
        self.props.audio_graph = AudioGraph()

        # Initialize WirePlumber
        self._init_wireplumber()

    def _init_wireplumber(self):
        """Initialize WirePlumber connection"""
        try:
            # Create core with proper configuration (Wp 0.5 API)
            self._wp_core = Wp.Core.new(None, None, None)

            # Connect core signals first
            self._wp_core.connect("connected", self._on_wp_connected)
            self._wp_core.connect("disconnected", self._on_wp_disconnected)

            # Setup object manager for nodes
            self._object_manager = Wp.ObjectManager.new()

            # Create proper interest for nodes
            node_interest = Wp.ObjectInterest.new_type(Wp.Node)
            self._object_manager.add_interest_full(node_interest)

            # Request proper features for nodes
            self._object_manager.request_object_features(Wp.Node, Wp.ProxyFeatures.BOUND)

            # Connect object manager signals
            self._object_manager.connect("object-added", self._on_wp_node_added)
            self._object_manager.connect("object-removed", self._on_wp_node_removed)

            # Install object manager
            self._wp_core.install_object_manager(self._object_manager)

            # Connect to WirePlumber
            if not self._wp_core.connect():
                print("Failed to connect to WirePlumber")
                self._connection_failed = True

        except Exception as e:
            print(f"Failed to initialize WirePlumber: {e}")
            self._connection_failed = True

    def _on_wp_connected(self, core):
        """WirePlumber connected - setup plugins"""
        try:
            print("WirePlumber connected, waiting for plugins...")

            # Use a timeout to wait for plugins to be available
            GLib.timeout_add(100, self._check_plugins_available)

        except Exception as e:
            print(f"Failed to setup WirePlumber plugins: {e}")
            self._connection_failed = True

    def _check_plugins_available(self):
        """Check if required plugins are available"""
        try:
            if not self._wp_core:
                return False

            # Try to find mixer API plugin
            if not self._mixer_api:
                # Use wp_plugin_find equivalent - search for plugin by name
                def find_mixer_api(obj, data):
                    try:
                        return hasattr(obj, "__gtype__") and "mixer" in str(obj.__gtype__).lower()
                    except:
                        return False

                self._mixer_api = self._wp_core.find_object(find_mixer_api, None)

            # Try to find default nodes API plugin
            if not self._defaults_api:

                def find_defaults_api(obj, data):
                    try:
                        return hasattr(obj, "__gtype__") and "default" in str(obj.__gtype__).lower()
                    except:
                        return False

                self._defaults_api = self._wp_core.find_object(find_defaults_api, None)

            # If we have the essential mixer API, we can proceed
            if self._mixer_api:
                print("Mixer API found, finalizing connection")
                self._finalize_connection()
                return False  # Stop timeout

            # Keep trying for a reasonable time
            self._pending_plugins = getattr(self, "_pending_plugins", 0) + 1
            if self._pending_plugins > 50:  # 5 seconds timeout
                print("Timeout waiting for plugins, proceeding anyway")
                self._finalize_connection()
                return False

            return True  # Continue timeout

        except Exception as e:
            print(f"Error checking plugins: {e}")
            self._finalize_connection()
            return False

    def _finalize_connection(self):
        """Finalize connection after all plugins are loaded"""
        # Configure mixer API if available
        if self._mixer_api:
            try:
                # Set cubic volume scale for better UX
                self._mixer_api.set_property("scale", 1)  # 1 = cubic scale
            except Exception as e:
                print(f"Failed to configure mixer API: {e}")

        # Thread-safe property updates
        def update_connection_state():
            self.props.connected = True
            self._is_ready = True
            self._connection_failed = False
            self.emit("connected")
            self.emit("connection-state-changed", True)
            return False

        GLib.idle_add(update_connection_state)

    def _on_wp_disconnected(self, core):
        """WirePlumber disconnected"""

        def update_disconnection_state():
            self.props.connected = False
            self._is_ready = False
            self._mixer_api = None
            self._defaults_api = None
            self.emit("disconnected")
            self.emit("connection-state-changed", False)
            return False

        GLib.idle_add(update_disconnection_state)

    def _on_wp_node_added(self, om, wp_node):
        """New WirePlumber node discovered"""
        try:
            # Extract node info
            node_id = wp_node.get_bound_id()
            props = wp_node.get_properties()
            media_class = props.get("media.class", "")

            # Create reactive AudioNode
            audio_node = AudioNode(node_id, self)
            audio_node.name = props.get("node.name", "")
            audio_node.description = props.get("node.description", "")
            audio_node.media_class = media_class

            # Get initial volume/mute state using mixer API
            self._get_initial_volume_state(audio_node, node_id)

            # Store WP node reference
            self._wp_nodes[node_id] = wp_node
            self._nodes[node_id] = wp_node  # Legacy compatibility

            # Add to appropriate collection (thread-safe)
            def add_to_collection():
                if media_class == "Audio/Sink":
                    self.sinks.add_node(audio_node)
                elif media_class == "Audio/Source":
                    self.sources.add_node(audio_node)
                elif media_class.startswith("Stream/"):
                    self.streams.add_node(audio_node)

                # Legacy compatibility signals
                self.emit("devices-changed")
                self.emit("streams-changed")
                return False

            GLib.idle_add(add_to_collection)

        except Exception as e:
            print(f"Error adding node {node_id}: {e}")

    def _get_initial_volume_state(self, audio_node, node_id):
        """Get initial volume and mute state for a node"""
        if not self._mixer_api:
            return

        try:
            # Use signal to get volume info
            variant = None
            self._mixer_api.emit("get-volume", node_id, variant)

            if variant:
                # Parse volume variant (can be double or vardict)
                if variant.get_type_string() == "d":
                    # Simple double volume
                    audio_node.volume = variant.get_double()
                elif variant.get_type_string() == "a{sv}":
                    # Dictionary with volume and mute
                    volume_dict = variant.unpack()
                    if "volume" in volume_dict:
                        audio_node.volume = volume_dict["volume"]
                    if "mute" in volume_dict:
                        audio_node.muted = volume_dict["mute"]

        except Exception as e:
            print(f"Failed to get initial volume for node {node_id}: {e}")

    def _on_wp_node_removed(self, om, wp_node):
        """WirePlumber node removed"""
        try:
            node_id = wp_node.get_bound_id()
            self._wp_nodes.pop(node_id, None)
            self._nodes.pop(node_id, None)  # Legacy compatibility

            # Remove from collections (thread-safe)
            def remove_from_collections():
                self.sinks.remove_node(node_id)
                self.sources.remove_node(node_id)
                self.streams.remove_node(node_id)

                # Legacy compatibility signals
                self.emit("devices-changed")
                self.emit("streams-changed")
                return False

            GLib.idle_add(remove_from_collections)

        except Exception as e:
            print(f"Error removing node {node_id}: {e}")

    def _set_wp_volume(self, node_id: int, volume: float):
        """Set volume in WirePlumber (called from AudioNode)"""
        if not self._mixer_api:
            print(f"Mixer API not available for setting volume on node {node_id}")
            return

        try:
            # Create volume variant as double
            volume_variant = GLib.Variant.new_double(volume)
            result = None

            # Use signal to set volume
            self._mixer_api.emit("set-volume", node_id, volume_variant, result)

            if result is False:
                print(f"Failed to set volume for node {node_id}")

        except Exception as e:
            print(f"Failed to set volume for node {node_id}: {e}")

    def _set_wp_mute(self, node_id: int, muted: bool):
        """Set mute in WirePlumber (called from AudioNode)"""
        if not self._mixer_api:
            print(f"Mixer API not available for setting mute on node {node_id}")
            return

        try:
            # Create mute variant as dictionary
            builder = GLib.VariantBuilder.new(GLib.VariantType.new("a{sv}"))
            builder.add_value(
                GLib.Variant.new_dict_entry(
                    GLib.Variant.new_string("mute"), GLib.Variant.new_variant(GLib.Variant.new_boolean(muted))
                )
            )
            mute_variant = builder.end()
            result = None

            # Use signal to set mute
            self._mixer_api.emit("set-volume", node_id, mute_variant, result)

            if result is False:
                print(f"Failed to set mute for node {node_id}")

        except Exception as e:
            print(f"Failed to set mute for node {node_id}: {e}")

    # ========== LEGACY API METHODS (blank implementations) ==========

    def set_default_sink(self, node_id: Union[int, str]) -> bool:
        """Set default output device by node ID or name"""
        if not self._defaults_api:
            return False

        try:
            # Convert string ID to int if needed
            if isinstance(node_id, str):
                # Try to find node by name
                for node in self.sinks.get_nodes():
                    if node.name == node_id:
                        node_id = node.node_id
                        break
                else:
                    return False

            # Use defaults API to set default sink
            self._defaults_api.emit("set-default-sink", node_id)
            return True

        except Exception as e:
            print(f"Failed to set default sink: {e}")
            return False

    def set_default_source(self, node_id: Union[int, str]) -> bool:
        """Set default input device by node ID or name"""
        if not self._defaults_api:
            return False

        try:
            # Convert string ID to int if needed
            if isinstance(node_id, str):
                # Try to find node by name
                for node in self.sources.get_nodes():
                    if node.name == node_id:
                        node_id = node.node_id
                        break
                else:
                    return False

            # Use defaults API to set default source
            self._defaults_api.emit("set-default-source", node_id)
            return True

        except Exception as e:
            print(f"Failed to set default source: {e}")
            return False

    def set_volume(self, node_id: Union[int, str], volume: float) -> bool:
        """Set volume for any node (device or stream). Volume: 0.0-1.0"""
        try:
            # Convert string ID to int if needed
            if isinstance(node_id, str):
                node_id = self._resolve_node_id(node_id)
                if node_id is None:
                    return False

            # Find the AudioNode and set volume (triggers WirePlumber update)
            audio_node = self._find_audio_node(node_id)
            if audio_node:
                audio_node.volume = max(0.0, min(1.0, volume))
                return True

            # Fallback: direct WirePlumber call
            self._set_wp_volume(node_id, volume)
            return True

        except Exception as e:
            print(f"Failed to set volume: {e}")
            return False

    def set_mute(self, node_id: Union[int, str], muted: bool) -> bool:
        """Set mute state for any node"""
        try:
            # Convert string ID to int if needed
            if isinstance(node_id, str):
                node_id = self._resolve_node_id(node_id)
                if node_id is None:
                    return False

            # Find the AudioNode and set mute (triggers WirePlumber update)
            audio_node = self._find_audio_node(node_id)
            if audio_node:
                audio_node.muted = muted
                return True

            # Fallback: direct WirePlumber call
            self._set_wp_mute(node_id, muted)
            return True

        except Exception as e:
            print(f"Failed to set mute: {e}")
            return False

    def toggle_mute(self, node_id: Union[int, str]) -> bool:
        """Toggle mute state for any node"""
        try:
            # Convert string ID to int if needed
            if isinstance(node_id, str):
                node_id = self._resolve_node_id(node_id)
                if node_id is None:
                    return False

            # Find the AudioNode and toggle mute
            audio_node = self._find_audio_node(node_id)
            if audio_node:
                audio_node.toggle_mute()
                return True

            return False

        except Exception as e:
            print(f"Failed to toggle mute: {e}")
            return False

    def get_volume(self, node_id: Union[int, str]) -> Optional[float]:
        """Get current volume for any node"""
        try:
            # Convert string ID to int if needed
            if isinstance(node_id, str):
                node_id = self._resolve_node_id(node_id)
                if node_id is None:
                    return None

            # Find the AudioNode and get volume
            audio_node = self._find_audio_node(node_id)
            if audio_node:
                return audio_node.volume

            return None

        except Exception as e:
            print(f"Failed to get volume: {e}")
            return None

    def get_mute_state(self, node_id: Union[int, str]) -> Optional[bool]:
        """Get current mute state for any node"""
        try:
            # Convert string ID to int if needed
            if isinstance(node_id, str):
                node_id = self._resolve_node_id(node_id)
                if node_id is None:
                    return None

            # Find the AudioNode and get mute state
            audio_node = self._find_audio_node(node_id)
            if audio_node:
                return audio_node.muted

            return None

        except Exception as e:
            print(f"Failed to get mute state: {e}")
            return None

    def get_volume_info(self, node_id: Union[int, str]) -> Optional[VolumeInfo]:
        """Get complete volume information for node"""
        pass

    def get_stream_by_pid(self, pid: int) -> Optional[AudioNodeInfo]:
        """Find audio stream by process ID"""
        pass

    def get_streams_by_app_name(self, app_name: str) -> List[AudioNodeInfo]:
        """Find all streams for application (e.g., 'firefox')"""
        pass

    def move_stream_to_device(self, stream_id: int, device_id: int) -> bool:
        """Move application stream to different device"""
        pass

    def set_stream_volume(self, stream_id: int, volume: float) -> bool:
        """Set per-application volume"""
        pass

    def set_stream_mute(self, stream_id: int, muted: bool) -> bool:
        """Set per-application mute"""
        pass

    def get_device_profiles(self, device_id: int) -> List[DeviceProfile]:
        """Get all available profiles for device"""
        pass

    def set_device_profile(self, device_id: int, profile_name: str) -> bool:
        """Set device profile (e.g., 'analog-stereo', 'pro-audio')"""
        pass

    def get_device_routes(self, device_id: int) -> List[DeviceRoute]:
        """Get all routes for device (headphones, speakers, line-out)"""
        pass

    def set_device_route(self, device_id: int, route_name: str) -> bool:
        """Set active route for device"""
        pass

    def create_virtual_sink(self, config: VirtualDeviceConfig) -> Optional[int]:
        """Create virtual output device for advanced routing"""
        pass

    def create_virtual_source(self, config: VirtualDeviceConfig) -> Optional[int]:
        """Create virtual input device"""
        pass

    def remove_virtual_device(self, node_id: int) -> bool:
        """Remove virtual device"""
        pass

    def create_link(
        self,
        output_node: int,
        input_node: int,
        output_port: Optional[str] = None,
        input_port: Optional[str] = None,
    ) -> Optional[AudioLink]:
        """Create direct audio connection between nodes"""
        pass

    def remove_link(self, link_id: int) -> bool:
        """Remove audio connection"""
        pass

    def get_node_ports(self, node_id: int) -> List[AudioPort]:
        """Get all ports for any node (for advanced channel routing)"""
        pass

    def get_node_info(self, node_id: int) -> Optional[AudioNodeInfo]:
        """Get complete node information with all properties"""
        pass

    def get_device_info(self, device_id: int) -> Optional[AudioDeviceInfo]:
        """Get complete device information"""
        pass

    def rename_node(self, node_id: int, name: str, description: Optional[str] = None) -> bool:
        """Set custom name/description for node (persistent)"""
        pass

    def get_node_by_name(self, name: str) -> Optional[AudioNodeInfo]:
        """Find node by its name property"""
        pass

    def search_nodes(self, **filters) -> List[AudioNodeInfo]:
        """Search nodes by properties (media_class, application_name, etc.)"""
        pass

    def save_volume_state(self, node_id: int) -> bool:
        """Manually save current volume/mute state (normally automatic)"""
        pass

    def restore_volume_state(self, node_id: int) -> bool:
        """Restore saved volume/mute state"""
        pass

    def get_persistent_settings(self) -> Dict[str, Any]:
        """Get all WirePlumber persistent settings"""
        pass

    def set_persistent_setting(self, key: str, value: Any) -> bool:
        """Set WirePlumber persistent setting (e.g., default volumes)"""
        pass

    def get_volume_as_percentage(self, node_id: Union[int, str]) -> Optional[int]:
        """Get volume as percentage (0-100) for UI display"""
        pass

    def set_volume_from_percentage(self, node_id: Union[int, str], percentage: int) -> bool:
        """Set volume from percentage (0-100)"""
        pass

    def increment_volume(self, node_id: Union[int, str], step: float = 0.05) -> bool:
        """Increase volume by step amount"""
        pass

    def decrement_volume(self, node_id: Union[int, str], step: float = 0.05) -> bool:
        """Decrease volume by step amount"""
        pass

    def get_icon_name(self, node_id: int) -> str:
        """Get appropriate icon name for node (for UI)"""
        pass

    def is_bluetooth_device(self, node_id: int) -> bool:
        """Check if node is Bluetooth device"""
        pass

    def is_usb_device(self, node_id: int) -> bool:
        """Check if node is USB device"""
        pass

    def get_device_type(self, node_id: int) -> str:
        """Get device type: 'internal', 'bluetooth', 'usb', 'hdmi', etc."""
        pass

    def get_node_name(self, node_id: Union[int, str]) -> str:
        """Get human-readable node name for UI display"""
        pass

    def get_sinks(self) -> List[Wp.Node]:
        """Get all output devices (Audio/Sink) as WP nodes"""
        pass

    def get_sources(self) -> List[Wp.Node]:
        """Get all input devices (Audio/Source) as WP nodes"""
        pass

    def get_sink_inputs(self) -> List[Wp.Node]:
        """Get all app output streams (Stream/Output/Audio) as WP nodes"""
        pass

    def get_source_outputs(self) -> List[Wp.Node]:
        """Get all app input streams (Stream/Input/Audio) as WP nodes"""
        pass

    # ========== HELPER METHODS ==========

    def _resolve_node_id(self, name: str) -> Optional[int]:
        """Resolve node name to node ID"""
        # Search in all collections
        for collection in [self.sinks, self.sources, self.streams]:
            for node in collection.get_nodes():
                if node.name == name or node.description == name:
                    return node.node_id
        return None

    def _find_audio_node(self, node_id: int) -> Optional[AudioNode]:
        """Find AudioNode by ID in all collections"""
        # Search in all collections
        for collection in [self.sinks, self.sources, self.streams]:
            node = collection.get_node(node_id)
            if node:
                return node
        return None


# ========== SINGLETON PATTERN ==========

_audio_service: Optional[AudioService] = None


def get_audio_service() -> AudioService:
    """Get global reactive audio service"""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service
